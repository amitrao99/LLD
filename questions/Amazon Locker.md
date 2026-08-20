## Draft 0 — Framing the problem

**What I opened with:** the service exposes two pathways — deposit and receive.
A locker contains slots, each slot has a size and an id. 
Size is the thing that decides whether a parcel fits.

**The question I asked myself:** do `LockerSize` and `ParcelSize` need to be separate
types, or does one size suffice?

**Conclusion — one shared enum.** Two separate enums would require a mapping table to
compare them, and that table would be an identity mapping I'd have to maintain forever.

**Refinements that came out of the discussion:**

boolean canFit(Parcel parcel)    { return size.canHold(parcel.size()); }   // physical
boolean canAccept(Parcel parcel) { return state == AVAILABLE && canFit(parcel); }


- **Be ready to defend discrete buckets over L×W×H.** Real dimensions pull you into
  orientation and rotation checks — 3D bin packing, which is not what's being tested.
  Physical lockers genuinely come in fixed sizes. State this as a deliberate choice
  rather than letting it look like a shortcut.

- **Naming ambiguity caught early:** I was using "Locker" for both the whole interface
  and the thing containing slots. 
  Split into `LockerStation` (the physical bank) → `LockerSlot` 

- **"Deposit and receive" hides the asymmetry.** The two operations aren't mirror images:

  - deposit = **allocation** — find a fitting free slot, reserve it, generate a code, notify

  - pickup = **authentication** — resolve a code, validate it, open the slot, release it

  It forces a `DepositTicket` entity linking parcel → slot → code → expiry,
  which is what makes everything else hang together.

---

## Draft 1 — First class sketch

```
enum SlotSize
Parcel[SlotSize, id]
LockerSlot[SlotSize, id]
LockerStation[List<LockerSlot>, id]
Reciept[LockerSlot, LockerStation, id, Parcel, long allocationTime, long withdrawlTime]

LockerStation {
    Optional<AllocationReciept> depositParcel();   // calls evictExpired
    Optional<WithdrawlReciept> withdrawParcel();
    private evictExpired();
}
```

**My open question:** one `Receipt` type holding both timestamps (withdrawal time null
until collected), or two separate receipt types?

**One-receipt-vs-two was the wrong framing.** My instinct to use one object was fine,
but the *name* was fighting me. A receipt is immutable proof that something happened.
What I described — mutable withdrawal time, null until it isn't — is a lifecycle entity.

Renamed to `DepositTicket` and gave it an explicit status:




```java
enum TicketStatus { ACTIVE, COLLECTED, EXPIRED, RETURNED }
```
Status matters more than the null check: `withdrawnAt == null` cannot distinguish
"waiting for pickup" from "expired, awaiting courier return," and those are different
states with different legal transitions. Once status exists, the null timestamps are
derived detail rather than load-bearing logic.


### What was wrong with this draft

**`withdrawParcel()` takes no arguments.** Biggest hole. There is no way to identify
which parcel is being collected. 

It needs `withdrawParcel(String pickupCode)`, 
and that implies the station needs a `Map<String, DepositTicket>` index — 
a `List<LockerSlot>` alone can't answer the question. Same for deposit: `depositParcel(Parcel parcel)`.



**Other corrections at this stage:**

- **`Optional<>` on both methods throws away the failure reason.** "No slot available,"
  "invalid code," and "code expired" are different problems with different handling.
  
  Typed exceptions read better and cost nothing.

- **`List<LockerSlot>` makes every allocation an O(n) scan.** `Map<SlotSize, Deque<LockerSlot>>`
  is O(1) per size class and makes best-fit trivial: walk sizes upward from the parcel's
  size, take the first non-empty bucket.
  
- **`evictExpired()` inside `depositParcel()` is a tradeoff worth naming.** Piggybacking on
  the request path means expiry only runs when there's traffic and adds latency to a
  user-facing call. Real systems use a scheduled sweeper. Deliberate simplification,
  stated as such.


- **Eviction does not empty the slot.** The parcel is physically still in there. Expiry is
  a bookkeeping event; the slot only frees when a human removes the box. This needs a
  separate `AWAITING_RETRIEVAL` slot state and a separate courier operation.


- **Open question deferred:** should `LockerStation` own code lookup at all? If customers
  can be routed to any station, codes must resolve globally, which argues for a
  `LockerService` layer holding the registry. Station-scoped is defensible — I chose it
  as a *stated assumption* rather than an accident.

---

## Draft 2 — The `ScrubbedDepositTicket` misstep

I needed the courier-facing return to not carry the pickup code, and proposed:

```java
ScrubbedDepositTicket extends DepositTicket
// constructor takes a DepositTicket and nulls out the pickupCode
```

**This was wrong, and it's a named smell.** `ScrubbedDepositTicket` is not a
`DepositTicket` — it's a `DepositTicket` with a hole in it. 

Anything holding a `DepositTicket` reference is entitled to assume `getPickupCode()` returns a code.

Mine returns null, so every consumer needs a null check the type system said was unnecessary, and the one that forgets it NPEs at runtime. Liskov violation.

Worse: it **fails open**. Add a sensitive field to the parent later and it leaks silently
until someone remembers to scrub it too.

**Rule extracted: never model a permission boundary with inheritance.** Subtyping is
for *adding* capability. Removing it by nulling is redaction-by-subclass.

**The fix — two records for two audiences:**

```java
record CourierDepositTicket(String ticketId, String slotId, String stationId, Instant depositedAt) {}
record CustomerPickupNotice(String ticketId, String pickupCode, String slotId, Instant expiresAt) {}
```

No inheritance, no nulls, no scrubbing. Each type carries exactly what its recipient may
see and the compiler enforces it. This also matches reality: the customer notice goes out
over SMS, not back through the courier's API response.

If a shared shape were needed for logging, a `sealed interface` would be the tool — not a
base class.

---

## Draft 3 — Strategies and key generation

```
LockerStation {
    SlotEligibilityStrategy
    SlotAllocationStrategy
    KeyGenService

    depositParcel(Parcel parcel, long time) {
        evictExpired();
        List<Slot> from SlotEligibilityStrategy
        Slot from SlotAllocationStrategy
        KeyGenService [while loop over generation + active key set]
        persist slot state and ticket
    }
}
```

**Good:** the strategy seams, and the status enum finally landing.

**What still needed cutting:**


- **`while (exists(generate()))` is unbounded and racy.** Unbounded: it can spin forever once
  the station saturates, with no signal anything is wrong → bounded retry (5), then fail
  loudly. Racy: check-then-act, two threads can both pass the check.


- **"Move to history" needed precision.** What gets removed is only the code→ticket index
  entry. The ticket itself stays queryable by id for audit. Two indexes, different lifetimes.



- **`EXPIRED → RETURNED` had no transition.** Both states existed in the enum but nothing
  could reach `RETURNED`, so expired parcels would occupy slots forever. Added
  `retrieveExpiredParcels(courierId)`.

---

Position: `Instant`/`Duration` in the domain model, epoch millis at the persistence
boundary if asked.

---

## Draft 4 — Closing the deposit path

**My claim:** deposit is done — generate a unique 6-digit key, keep an active key set,
check membership, insert.

**Two gaps:**

1. **Nothing bound the parcel to a recipient.** `depositParcel(Parcel)` generated a code and
   returned it *to the courier*. There was no customer in the model, so the code had
   nowhere to go. 
   
   Added `recipientId` to `Parcel` and a `NotificationService` call. 
   
   This is also what finally makes the two-record split pay off — `CourierDepositTicket` returns to
   the caller, `CustomerPickupNotice` goes to notification.

**`DEFFERED FOR LATER`**
2. **The uniqueness check was still check-then-act.** Fixed by making insertion *be* the
   check.

**`ConcurrentHashMap` correction:** I'd assumed `putIfAbsent` throws on collision. It does
not — it returns the existing value, or `null` if the insert won. `computeIfAbsent` returns
the existing value and simply skips the lambda. Neither throws. You branch on the return.

Also: `synchronized` and `ConcurrentHashMap` are not interchangeable here. The map gives
atomicity *per key*; allocating a slot and inserting the ticket is a multi-step operation
that needs its own protection.

**`DEFFERED FOR LATER`**


**Code security answer to have ready:** 6 digits is 10⁶, and an attacker at a keypad doesn't
need a *specific* code — any active one opens a door. 

With 40 occupied slots that's 40/10⁶ per guess. Mitigations: rate limit the keypad, lock out after N failures, scope codes per
station so a code stolen at one is useless at another.

---

## Draft 5 — Writing it out surfaced a real bug

`sweepExpired()` runs at the top of `withdrawParcel()`, and the first version removed
expired entries from `activeByCode`. Consequence: the lookup immediately after always
returned null, so `ExpiredPickupCodeException` was **unreachable** — every expired code
came back as "unrecognised code."

Wrong message for the customer standing at the keypad, who deserves "this expired Tuesday
and is being returned."

**Fix:** the sweep marks status and sets the slot to `AWAITING_RETRIEVAL`, but leaves the
index entry alone. The code is only released when the courier retrieves the parcel. This
is also the more correct model — the code genuinely isn't reusable while the box is still
sitting in the slot.

Worth narrating in an interview: it's a bug that only appears once you write the *sequence*,
not the class diagram.



```java
import java.time.Duration;
import java.time.Instant;
import java.util.*;


enum SlotSize {
    SMALL, MEDIUM, LARGE, EXTRA_LARGE;

    boolean canHold(SlotSize parcelSize) {
        return this.ordinal() >= parcelSize.ordinal();
    }
}

enum SlotState {
    AVAILABLE,
    RESERVED,             // allocated by system, parcel not yet physically inside
    OCCUPIED,
    AWAITING_RETRIEVAL,   // expired parcel still physically in the slot
    OUT_OF_SERVICE
}

enum TicketStatus {
    ACTIVE, COLLECTED, EXPIRED, RETURNED
}

class Parcel {
    private final String id;
    private final SlotSize size;
    private final String recipientId;

    Parcel(String id, SlotSize size, String recipientId) {
        this.id = id;
        this.size = size;
        this.recipientId = recipientId;
    }

    String getId() { return id; }
    SlotSize getSize() { return size; }
    String getRecipientId() { return recipientId; }

    @Override
    public String toString() { return "Parcel[" + id + ", " + size + ", for " + recipientId + "]"; }
}


class CourierDepositTicket {
    private final String ticketId;
    private final String slotId;
    private final String stationId;
    private final Instant depositedAt;

    CourierDepositTicket(String ticketId, String slotId, String stationId, Instant depositedAt) {
        this.ticketId = ticketId;
        this.slotId = slotId;
        this.stationId = stationId;
        this.depositedAt = depositedAt;
    }

    String getTicketId() { return ticketId; }
    String getSlotId() { return slotId; }
    String getStationId() { return stationId; }
    Instant getDepositedAt() { return depositedAt; }

    @Override
    public String toString() {
        return "CourierDepositTicket[slot=" + slotId + ", station=" + stationId + "]";
    }
}

class CustomerPickupNotice {
    private final String ticketId;
    private final String pickupCode;
    private final String slotId;
    private final Instant expiresAt;

    CustomerPickupNotice(String ticketId, String pickupCode, String slotId, Instant expiresAt) {
        this.ticketId = ticketId;
        this.pickupCode = pickupCode;
        this.slotId = slotId;
        this.expiresAt = expiresAt;
    }

    String getTicketId() { return ticketId; }
    String getPickupCode() { return pickupCode; }
    String getSlotId() { return slotId; }
    Instant getExpiresAt() { return expiresAt; }
}

class WithdrawalReceipt {
    private final String ticketId;
    private final String slotId;
    private final Instant withdrawnAt;

    WithdrawalReceipt(String ticketId, String slotId, Instant withdrawnAt) {
        this.ticketId = ticketId;
        this.slotId = slotId;
        this.withdrawnAt = withdrawnAt;
    }

    String getTicketId() { return ticketId; }
    String getSlotId() { return slotId; }
    Instant getWithdrawnAt() { return withdrawnAt; }

    @Override
    public String toString() {
        return "WithdrawalReceipt[slot=" + slotId + ", at=" + withdrawnAt + "]";
    }
}

class LockerSlot {
    private final String id;
    private final SlotSize size;
    private SlotState state = SlotState.AVAILABLE;

    LockerSlot(String id, SlotSize size) {
        this.id = id;
        this.size = size;
    }

    String getId() { return id; }
    SlotSize getSize() { return size; }
    SlotState getState() { return state; }
    void setState(SlotState s) { this.state = s; }

    boolean canFit(Parcel parcel) {
        return size.canHold(parcel.getSize());
    }

    boolean canAccept(Parcel parcel) {
        return state == SlotState.AVAILABLE && canFit(parcel);
    }

    void openDoor() {
        System.out.println("  [hardware] slot " + id + " door opens");
    }
}

/**
 * WHY THIS CLASS EXISTS
 *
 * A parcel goes into a slot, and a customer comes back hours later holding only
 * a code. Nothing else in the model can answer "which slot does this code open,
 * and is it still allowed to?" - the slot knows it is occupied but not by whom,
 * the parcel knows its recipient but not where it ended up. DepositTicket is the
 * join between them, and the code is its lookup key.
 *
 * THE FOUR QUESTIONS IT MUST ANSWER
 *   1. code -> which slot?          pickupCode + slot
 *   2. is this code still valid?    status + expiresAt
 *   3. whose parcel is this?        parcel -> recipientId
 *   4. what happened, and when?     allocatedAt, withdrawnAt, status   (audit)
 *
 * WHY IT IS AN ENTITY AND NOT A RECEIPT
 * A receipt is immutable proof of a past event. This thing MUTATES along a
 * lifecycle: ACTIVE -> COLLECTED, or ACTIVE -> EXPIRED -> RETURNED. The objects
 * handed to the courier and the customer are read-only VIEWS taken off this one
 * at a moment in time - which is exactly why they can each carry a different
 * subset of the fields.
 *
 * WHY status, AND NOT JUST NULL TIMESTAMPS
 * withdrawnAt == null cannot tell "waiting for pickup" apart from "expired, box
 * still sitting in the slot awaiting courier return". Those are different states
 * with different legal next moves, so they need distinct names, not a null check.
 */
class DepositTicket {
    private final String id;
    private final String pickupCode;
    private final Parcel parcel;
    private final LockerSlot slot;
    private final Instant allocatedAt;
    private final Instant expiresAt;
    private Instant withdrawnAt;                       // null until collected
    private TicketStatus status = TicketStatus.ACTIVE;

    DepositTicket(String id, String pickupCode, Parcel parcel, LockerSlot slot,
                  Instant allocatedAt, Instant expiresAt) {
        this.id = id;
        this.pickupCode = pickupCode;
        this.parcel = parcel;
        this.slot = slot;
        this.allocatedAt = allocatedAt;
        this.expiresAt = expiresAt;
    }

    String getId() { return id; }
    String getPickupCode() { return pickupCode; }
    Parcel getParcel() { return parcel; }
    LockerSlot getSlot() { return slot; }
    Instant getAllocatedAt() { return allocatedAt; }
    Instant getExpiresAt() { return expiresAt; }
    Instant getWithdrawnAt() { return withdrawnAt; }
    TicketStatus getStatus() { return status; }

    boolean isExpiredAt(Instant now) { return now.isAfter(expiresAt); }

    void markCollected(Instant now) {
        this.status = TicketStatus.COLLECTED;
        this.withdrawnAt = now;
    }
    void markExpired() { this.status = TicketStatus.EXPIRED; }
    void markReturned() { this.status = TicketStatus.RETURNED; }
}

// ---------------------------------------------------------------------------
// Failure modes
// ---------------------------------------------------------------------------

/*
 * Typed exceptions, not Optional.empty().
 * Optional collapses "no slot available", "unknown code", "already collected"
 * and "expired" into one indistinguishable absence. The customer standing at the
 * keypad deserves "this expired on Tuesday and has gone back to the courier",
 * not a generic beep.
 */
class NoAvailableSlotException extends RuntimeException {
    NoAvailableSlotException(String m) { super(m); }
}
class InvalidPickupCodeException extends RuntimeException {
    InvalidPickupCodeException(String m) { super(m); }
}
class ExpiredPickupCodeException extends RuntimeException {
    ExpiredPickupCodeException(String m) { super(m); }
}
class AlreadyCollectedException extends RuntimeException {
    AlreadyCollectedException(String m) { super(m); }
}
class CodeGenerationException extends RuntimeException {
    CodeGenerationException(String m) { super(m); }
}

// ---------------------------------------------------------------------------
// Slot index
// ---------------------------------------------------------------------------

/**
 * WHY THIS CLASS EXISTS
 *
 * The first draft had LockerStation hold a plain List<LockerSlot>. Every deposit
 * then meant scanning the entire list asking "free? big enough?" - O(n) per
 * deposit. Worse, the logic for putting a slot BACK ends up smeared across
 * withdraw, the expiry sweep, and courier retrieval: three separate places that
 * all have to remember to do it correctly.
 *
 * SlotIndex exists so there is ONE owner of "which slots are free right now".
 * It holds two structures because they answer two different questions:
 *
 *   freeBySize : SlotSize -> list of currently FREE slots of that size
 *                One hash lookup instead of a scan, and it makes best-fit
 *                natural: start at the parcel's own size and walk upward until
 *                a bucket has something in it.
 *
 *   allSlots   : id -> every slot, free or not
 *                Needed for reporting, admin, and marking a slot out of service.
 *                The free list alone cannot answer "show me the whole station",
 *                because occupied slots are absent from it by definition.
 *
 * THE INVARIANT THAT JUSTIFIES THE CLASS
 * A slot appears in freeBySize IF AND ONLY IF its state is AVAILABLE. Every
 * claim or release goes through claim() / markFree(), which change the list and
 * the state together. A bare Map on the station would let one caller flip the
 * state and forget the list, and the two would drift apart silently. Owning that
 * invariant in one place is the real reason this class exists - the O(1) lookup
 * is a bonus.
 *
 * Plain HashMap, not EnumMap: EnumMap is array-backed and marginally faster, but
 * SlotSize has four constants so the difference is noise.
 */
class SlotIndex {
    private final Map<SlotSize, List<LockerSlot>> freeBySize = new HashMap<>();
    private final Map<String, LockerSlot> allSlots = new HashMap<>();

    SlotIndex(List<LockerSlot> slots) {
        // Seed every size up front, so getFreeSlotsOfSize never returns null.
        for (SlotSize size : SlotSize.values()) {
            freeBySize.put(size, new ArrayList<>());
        }
        for (LockerSlot slot : slots) {
            allSlots.put(slot.getId(), slot);
            freeBySize.get(slot.getSize()).add(slot);
        }
    }

    List<LockerSlot> getFreeSlotsOfSize(SlotSize size) {
        return freeBySize.get(size);
    }

    /** Take a slot out of the free pool. State and list change together. */
    void claim(LockerSlot slot) {
        freeBySize.get(slot.getSize()).remove(slot);
        slot.setState(SlotState.RESERVED);
    }

    /** Put a slot back in the free pool. State and list change together. */
    void markFree(LockerSlot slot) {
        slot.setState(SlotState.AVAILABLE);
        List<LockerSlot> bucket = freeBySize.get(slot.getSize());
        if (!bucket.contains(slot)) {
            bucket.add(slot);
        }
    }

    Collection<LockerSlot> getAllSlots() { return allSlots.values(); }
}

// ---------------------------------------------------------------------------
// Slot selection: eligibility, then allocation
// ---------------------------------------------------------------------------

/**
 * STAGE 1 - "which slots COULD take this parcel?"
 *
 * Pure filtering, no preference. This is where physical constraints live, and
 * where new ones get added: size today; weight rating, refrigeration, or an
 * accessible-height requirement tomorrow. A slot excluded here is one the parcel
 * must never end up in, whatever the ranking says.
 */
interface SlotEligibilityStrategy {
    List<LockerSlot> findEligible(SlotIndex index, Parcel parcel);
}

/**
 * STAGE 2 - "of those, which one do we PICK?"
 *
 * Pure preference, no filtering. Everything passed in is already known to work,
 * so this only has to rank. Swapping the ranking - best-fit, even wear across
 * slots, nearest to the door for a customer with accessibility needs - cannot
 * break a correctness rule, because correctness was settled in stage 1.
 *
 * The split is worth the extra interface precisely because the two kinds of
 * change have different blast radius: a new constraint is a safety change, a new
 * ranking is a policy change.
 */
interface SlotAllocationStrategy {
    Optional<LockerSlot> choose(List<LockerSlot> eligible, Parcel parcel);
}

/**
 * Eligible = free, and big enough. Walks size buckets upward from the parcel's
 * own size, so a SMALL parcel is eligible for every size, but a LARGE parcel is
 * never offered a SMALL slot.
 */
class SizeBasedEligibilityStrategy implements SlotEligibilityStrategy {
    @Override
    public List<LockerSlot> findEligible(SlotIndex index, Parcel parcel) {
        List<LockerSlot> eligible = new ArrayList<>();
        SlotSize[] sizes = SlotSize.values();
        for (int i = parcel.getSize().ordinal(); i < sizes.length; i++) {
            for (LockerSlot slot : index.getFreeSlotsOfSize(sizes[i])) {
                if (slot.canAccept(parcel)) {
                    eligible.add(slot);
                }
            }
        }
        return eligible;
    }
}

/** Smallest slot that fits, so we don't burn an EXTRA_LARGE on a padded envelope. */
class BestFitAllocationStrategy implements SlotAllocationStrategy {
    @Override
    public Optional<LockerSlot> choose(List<LockerSlot> eligible, Parcel parcel) {
        LockerSlot best = null;
        for (LockerSlot slot : eligible) {
            if (best == null || slot.getSize().ordinal() < best.getSize().ordinal()) {
                best = slot;
            }
        }
        return Optional.ofNullable(best);
    }
}

// ---------------------------------------------------------------------------
// Pickup codes
// ---------------------------------------------------------------------------

/**
 * PURE generator. One job: hand back a random 6-digit string.
 *
 * It knows nothing about uniqueness, live codes, retries or collisions. Those
 * belong to the station, because the station is what owns the set of live codes.
 * Keeping the generator ignorant of that set means there is nothing here to
 * contend on, nothing to lock, and nothing to test beyond "is it six digits".
 *
 * Security note for the interviewer: 6 digits is 10^6, and an attacker at the
 * keypad doesn't need a SPECIFIC code - any live one opens a door. With 40
 * occupied slots that is 40/10^6 per guess, which adds up over a long session.
 * Mitigations: rate-limit the keypad, lock out after N failures, and keep codes
 * station-scoped so a code stolen at one station is useless at another.
 */
class PickupCodeGenerator {
    private static final int CODE_LENGTH = 6;
    private final Random random;

    PickupCodeGenerator(Random random) {
        this.random = random;
    }

    String generate() {
        StringBuilder sb = new StringBuilder(CODE_LENGTH);
        for (int i = 0; i < CODE_LENGTH; i++) {
            sb.append(random.nextInt(10));
        }
        return sb.toString();
    }
}

// ---------------------------------------------------------------------------
// Notification
// ---------------------------------------------------------------------------

/** Stubbed. The point is that the call EXISTS - otherwise the customer never learns the code. */
interface NotificationService {
    void notifyRecipient(String recipientId, CustomerPickupNotice notice);
}

class ConsoleNotificationService implements NotificationService {
    @Override
    public void notifyRecipient(String recipientId, CustomerPickupNotice notice) {
        TestPeek.lastCode = notice.getPickupCode();
        TestPeek.byRecipient.put(recipientId, notice.getPickupCode());
        System.out.println("  [sms -> " + recipientId + "] Parcel ready in slot "
                + notice.getSlotId() + ". Code: " + notice.getPickupCode()
                + ". Collect by " + notice.getExpiresAt());
    }
}

// ---------------------------------------------------------------------------
// Station
// ---------------------------------------------------------------------------

class LockerStation {

    private static final int MAX_CODE_ATTEMPTS = 5;

    private final String id;
    private final SlotIndex slotIndex;
    private final SlotEligibilityStrategy eligibilityStrategy;
    private final SlotAllocationStrategy allocationStrategy;
    private final PickupCodeGenerator codeGenerator;
    private final NotificationService notificationService;
    private final Duration pickupWindow;

    /*
     * TWO indexes with DIFFERENT lifetimes:
     *  - activeByCode : code -> ticket. The entry is removed once the parcel
     *    leaves the slot (collected, or returned to the courier). That removal is
     *    what frees the code for reuse.
     *  - ticketsById  : permanent audit trail, survives collection.
     * Removing from activeByCode is right, but it means a code alone can no
     * longer resolve history. Hence the second map.
     */
    private final Map<String, DepositTicket> activeByCode = new HashMap<>();
    private final Map<String, DepositTicket> ticketsById = new HashMap<>();

    LockerStation(String id, List<LockerSlot> slots,
                  SlotEligibilityStrategy eligibilityStrategy,
                  SlotAllocationStrategy allocationStrategy,
                  PickupCodeGenerator codeGenerator,
                  NotificationService notificationService,
                  Duration pickupWindow) {
        this.id = id;
        this.slotIndex = new SlotIndex(slots);
        this.eligibilityStrategy = eligibilityStrategy;
        this.allocationStrategy = allocationStrategy;
        this.codeGenerator = codeGenerator;
        this.notificationService = notificationService;
        this.pickupWindow = pickupWindow;
    }

    CourierDepositTicket depositParcel(Parcel parcel) {
        sweepExpired();

        /*
         * [RACE] Everything from here down to activeByCode.put() is one logical
         * transaction. Two couriers depositing at once can interleave between
         * choosing a slot and claiming it. A station is small and deposits are
         * infrequent, so station-level locking around this block is the cheapest
         * defensible answer - nothing finer is justified.
         */
        List<LockerSlot> eligible = eligibilityStrategy.findEligible(slotIndex, parcel);
        LockerSlot slot = allocationStrategy.choose(eligible, parcel)
                .orElseThrow(() -> new NoAvailableSlotException(
                        "No free slot of size " + parcel.getSize() + " or larger at station " + id));

        slotIndex.claim(slot);

        Instant allocatedAt = Instant.now();
        String code = generateUniqueCode();
        String ticketId = UUID.randomUUID().toString();

        DepositTicket ticket = new DepositTicket(
                ticketId, code, parcel, slot, allocatedAt, allocatedAt.plus(pickupWindow));

        activeByCode.put(code, ticket);
        ticketsById.put(ticketId, ticket);

        slot.openDoor();
        slot.setState(SlotState.OCCUPIED);   // courier has physically placed the parcel

        // The customer half goes out of band. The courier never sees the code.
        notificationService.notifyRecipient(
                parcel.getRecipientId(),
                new CustomerPickupNotice(ticketId, code, slot.getId(), ticket.getExpiresAt()));

        return new CourierDepositTicket(ticketId, slot.getId(), id, allocatedAt);
    }

    /*
     * Uniqueness lives HERE, not in the generator, because this is what owns the
     * live-code set.
     *
     * BOUNDED retry, not `while (exists(generate()))`. An unbounded loop spins
     * forever once the station saturates and gives no signal that anything is
     * wrong. Five attempts, then fail loudly.
     *
     * [RACE] containsKey() then put() is check-then-act: two threads can both
     * pass the check for the same code. The concurrent fix is to let the INSERT
     * be the check - putIfAbsent on a ConcurrentHashMap returns the existing
     * value on collision (it does NOT throw), so there is no window between
     * checking and claiming.
     */
    private String generateUniqueCode() {
        for (int attempt = 0; attempt < MAX_CODE_ATTEMPTS; attempt++) {
            String candidate = codeGenerator.generate();
            if (!activeByCode.containsKey(candidate)) {
                return candidate;
            }
        }
        throw new CodeGenerationException(
                "Could not generate a unique code after " + MAX_CODE_ATTEMPTS + " attempts");
    }

    WithdrawalReceipt withdrawParcel(String pickupCode) {
        sweepExpired();

        DepositTicket ticket = activeByCode.get(pickupCode);
        if (ticket == null) {
            // Deliberately vague to the user, specific in logs - don't confirm to
            // a guesser whether a code ever existed.
            throw new InvalidPickupCodeException("Unrecognised pickup code");
        }
        if (ticket.getStatus() == TicketStatus.COLLECTED) {
            throw new AlreadyCollectedException("Parcel already collected at " + ticket.getWithdrawnAt());
        }
        if (ticket.getStatus() == TicketStatus.EXPIRED || ticket.isExpiredAt(Instant.now())) {
            throw new ExpiredPickupCodeException(
                    "Code expired at " + ticket.getExpiresAt() + "; parcel is going back to the courier");
        }

        LockerSlot slot = ticket.getSlot();
        slot.openDoor();
        slotIndex.markFree(slot);

        ticket.markCollected(Instant.now());
        activeByCode.remove(pickupCode);      // frees the code; ticketsById keeps the record

        return new WithdrawalReceipt(ticket.getId(), slot.getId(), ticket.getWithdrawnAt());
    }

    /*
     * Piggybacking the sweep on the request path means expiry only runs when
     * there is traffic, and it adds latency to a user-facing call. A real system
     * runs this on a scheduler. Inline here for simplicity - a deliberate
     * simplification, not an accident.
     */
    private void sweepExpired() {
        Instant now = Instant.now();
        for (DepositTicket ticket : activeByCode.values()) {
            if (ticket.getStatus() == TicketStatus.ACTIVE && ticket.isExpiredAt(now)) {
                ticket.markExpired();
                /*
                 * The slot does NOT become AVAILABLE here. The parcel is still
                 * physically in it. Expiry is a bookkeeping event; the slot only
                 * frees once a human removes the box.
                 */
                ticket.getSlot().setState(SlotState.AWAITING_RETRIEVAL);
                /*
                 * We deliberately do NOT drop the code from activeByCode here.
                 * The first draft did, which made ExpiredPickupCodeException
                 * unreachable - the sweep runs before the lookup, so every expired
                 * code came back as "unrecognised". Keeping the entry until the
                 * courier collects is what lets us tell the customer the truth.
                 */
            }
        }
    }

    /**
     * The EXPIRED -> RETURNED transition. Without this, expired parcels occupy
     * their slots forever and RETURNED is a state nothing can reach.
     */
    List<String> retrieveExpiredParcels(String courierId) {
        sweepExpired();
        List<String> emptied = new ArrayList<>();
        for (DepositTicket ticket : ticketsById.values()) {
            if (ticket.getStatus() == TicketStatus.EXPIRED) {
                LockerSlot slot = ticket.getSlot();
                slot.openDoor();
                slotIndex.markFree(slot);
                ticket.markReturned();
                activeByCode.remove(ticket.getPickupCode());   // only now is the code reusable
                emptied.add(slot.getId());
            }
        }
        System.out.println("  [courier " + courierId + "] retrieved " + emptied.size() + " expired parcel(s)");
        return emptied;
    }

    void printSlotStates() {
        StringBuilder sb = new StringBuilder("  station " + id + ": ");
        List<LockerSlot> sorted = new ArrayList<>(slotIndex.getAllSlots());
        sorted.sort(Comparator.comparing(LockerSlot::getId));
        for (LockerSlot s : sorted) {
            sb.append(s.getId()).append("=").append(s.getState()).append("  ");
        }
        System.out.println(sb);
    }
}

// ---------------------------------------------------------------------------
// Runnable walkthrough
// ---------------------------------------------------------------------------

public class LockerSystem {

    private static LockerStation newStation(String id, List<LockerSlot> slots, Duration window) {
        return new LockerStation(
                id, slots,
                new SizeBasedEligibilityStrategy(),
                new BestFitAllocationStrategy(),
                new PickupCodeGenerator(new Random()),
                new ConsoleNotificationService(),
                window);
    }

    public static void main(String[] args) throws InterruptedException {

        List<LockerSlot> slots = new ArrayList<>();
        slots.add(new LockerSlot("S1", SlotSize.SMALL));
        slots.add(new LockerSlot("S2", SlotSize.SMALL));
        slots.add(new LockerSlot("M1", SlotSize.MEDIUM));
        slots.add(new LockerSlot("L1", SlotSize.LARGE));

        LockerStation station = newStation("BHM-01", slots, Duration.ofHours(48));

        System.out.println("=== 1. deposit + collect ===");
        CourierDepositTicket d1 = station.depositParcel(new Parcel("P1", SlotSize.SMALL, "alice"));
        System.out.println("  courier receives: " + d1 + "   (no code, by design)");
        station.printSlotStates();

        // A real customer reads the code off their phone; reaching into the
        // notification stub is a test shortcut.
        WithdrawalReceipt r1 = station.withdrawParcel(TestPeek.lastCode);
        System.out.println("  withdrawn: " + r1);
        station.printSlotStates();

        System.out.println("\n=== 2. best fit upsizes when it has to ===");
        station.depositParcel(new Parcel("P2", SlotSize.SMALL, "bob"));
        station.depositParcel(new Parcel("P3", SlotSize.SMALL, "carol"));
        // Both SMALL slots are now taken, so a SMALL parcel must spill into MEDIUM.
        CourierDepositTicket d4 = station.depositParcel(new Parcel("P4", SlotSize.SMALL, "dave"));
        System.out.println("  P4 (SMALL) placed in: " + d4.getSlotId() + "   <- upsized");

        System.out.println("\n=== 3. station full ===");
        station.depositParcel(new Parcel("P5", SlotSize.LARGE, "erin"));    // takes L1
        try {
            station.depositParcel(new Parcel("P6", SlotSize.LARGE, "frank"));
        } catch (NoAvailableSlotException e) {
            System.out.println("  rejected: " + e.getMessage());
        }

        System.out.println("\n=== 4. unknown code ===");
        try {
            station.withdrawParcel("000000");
        } catch (InvalidPickupCodeException e) {
            System.out.println("  rejected: " + e.getMessage());
        }

        /*
         * The expiry demo needs a SECOND station with a one-second pickup window
         * and a real sleep, because time now comes from Instant.now() and cannot
         * be moved. This is the cost of dropping the injected Clock: the only way
         * to exercise expiry is to actually wait for it.
         */
        System.out.println("\n=== 5. expiry -> courier retrieval ===");
        List<LockerSlot> shortSlots = new ArrayList<>();
        shortSlots.add(new LockerSlot("X1", SlotSize.MEDIUM));
        LockerStation shortStation = newStation("BHM-02", shortSlots, Duration.ofSeconds(1));

        shortStation.depositParcel(new Parcel("P7", SlotSize.SMALL, "grace"));
        String graceCode = TestPeek.lastCode;

        System.out.println("  waiting for the pickup window to lapse...");
        Thread.sleep(1500);

        try {
            shortStation.withdrawParcel(graceCode);
        } catch (ExpiredPickupCodeException e) {
            System.out.println("  rejected: " + e.getMessage());
        }
        shortStation.printSlotStates();
        shortStation.retrieveExpiredParcels("courier-77");
        shortStation.printSlotStates();
    }
}

/** Test scaffolding to observe codes that would normally leave over SMS. */
class TestPeek {
    static String lastCode;
    static final Map<String, String> byRecipient = new HashMap<>();

    static String codeFor(String recipient) { return byRecipient.get(recipient); }
}














The winner is decided by hardware, and it's arbitrary — whichever thread's atomic instruction lands first. Nothing about your code influences it. Here's the mechanism.

`ConcurrentHashMap` is an array of bins. `putIfAbsent(code, ticket)` hashes the code to a bin index, then:

- **Bin is empty** → the thread attempts a **CAS** (compare-and-swap): "install my node *only if* this slot is still null." CAS is a single atomic CPU instruction. Two threads issuing it against the same address, one succeeds, one fails — the hardware guarantees exactly one. The loser doesn't error out; its CAS just returns false, it loops, now sees a non-null bin, and takes the path below.
- **Bin is non-empty** → the thread takes a lock on that bin's first node, walks the chain, and either finds the key (returns the existing value) or appends (returns null).

```
```java
private String claimUniqueCode(DepositTicket ticket) {
    for (int attempt = 0; attempt < MAX_CODE_ATTEMPTS; attempt++) {
        String candidate = codeGenerator.generate();
        // null  -> nobody had this code, I own it now
        // non-null -> someone else got here first, that's their ticket
        if (activeByCode.putIfAbsent(candidate, ticket) == null) {
            return candidate;
        }
    }
    throw new CodeGenerationException("No unique code after " + MAX_CODE_ATTEMPTS + " attempts");
}
```

Contrast with what you have now:

```java
if (!activeByCode.containsKey(candidate)) {   // thread A checks: free
    return candidate;                          // thread B checks: also free
}                                              // both proceed with the same code
```


The gap between the check and the claim is where both threads pass. `putIfAbsent` has no gap — the check *is* the write, one indivisible operation. That's the entire fix.

Note the signature change: the ticket has to be built *before* you claim the code, since you're inserting it as part of the claim. Currently you generate the code first and construct the ticket after, so you'd reorder — build the ticket with a placeholder code, or restructure so the code is claimed against the ticket object.

**On `synchronized` vs the map:** same arbitrariness, different scope. The JVM monitor picks a winner among blocked threads with no ordering guarantee either. The difference is what's protected. `putIfAbsent` protects one key. Your deposit is *choose slot → claim slot → claim code → insert ticket* — four steps that must not interleave. Per-key atomicity does nothing for that; two couriers can still be handed the same slot. So you need both: `synchronized` on the deposit method for the multi-step transaction, and `ConcurrentHashMap` underneath if you ever want reads to proceed without blocking.

For the interview, the useful sentence is: *"I don't need to know which thread wins — I need exactly one to win and the other to be told, and `putIfAbsent`'s return value is how it's told."*





**The real point: retries don't defend against the thing that would actually break this.** They defend against bad luck, and bad luck isn't the threat. The threat is high occupancy — and if occupancy is high, *every* attempt has the same elevated probability, so more retries just means more failures before you give up. The fix for a crowded code space is more digits (7 digits = 10× the room), not more spins.

So treat the constant as a **tripwire, not a margin**. If it ever trips with 40 slots and a 10⁶ space, the cause isn't randomness — it's a bug. Almost certainly codes aren't being released: your `activeByCode` grows forever because some path forgets to remove. That's exactly the kind of leak worth alerting on rather than papering over.

Which means the exception message should say so:

```java
throw new CodeGenerationException(
    "No unique code after " + MAX_CODE_ATTEMPTS + " attempts at station " + id
    + " (active codes: " + activeByCode.size() + "). "
    + "Expected impossible at normal occupancy - check for leaked codes.");
```




Correct on both counts, and the second point is the stronger argument.

**`putIfAbsent` becomes redundant.** If every mutation of `activeByCode` happens while holding the station monitor, then `containsKey` + `put` inside that block is already indivisible with respect to any other deposit. `putIfAbsent` would be re-solving, at the key level, a problem the lock already solved at the transaction level. I'd cut it — leaving it in isn't harmless, because a reader may assume the map is providing safety that's actually coming from the lock, and then "optimize away" the lock later.

**And your reasoning for why is the right one.** The invariant spans two data structures: a slot claimed with no code bound is a stranded slot, a code bound with no slot claimed is a code pointing at nothing. `putIfAbsent` can only make *one* of those atomic. An atomic operation on half of an invariant is worthless. Once you've said "these two writes must succeed or fail together," you've already ruled out per-key atomicity as the mechanism — the only tool with the right scope is mutual exclusion over both.

So I'd revise my step 4. Instead:

**Every method that touches `activeByCode` or `slotIndex` must hold the same monitor** — not just `depositParcel`. That's `withdrawParcel`, `sweepExpired`, and `retrieveExpiredParcels` too. My earlier version only synchronized deposit, which leaves a real hole: a withdrawal removing a code while a deposit is mid-check is the same class of race, just with a different pair of threads. One lock, four entry points. Note `sweepExpired` is called from the others, so it's already covered by reentrancy — mark it anyway for the reader.

That also settles `ConcurrentHashMap`: with all mutators serialized, plain `HashMap` is fine. It'd only pay off if you had lock-free *read* paths (a "check my parcel status" query that never writes), which this design doesn't have.

Two things to keep ready for pushback:

**"Isn't one lock per station too coarse?"** No — a station has ~40 slots and deposits arrive minutes apart. The critical section is a few map operations, microseconds. Contention is effectively zero, and the code is obviously correct, which is worth more than throughput nobody needs.

**"What if you had to remove the lock?"** Then you'd need the slot claim atomic too — a CAS on slot state, `AVAILABLE → RESERVED`, so exactly one thread wins the slot — *then* `putIfAbsent` for the code, *then* compensating release of the slot if the code claim fails. That's when `putIfAbsent` earns its place. It's a worse design here, but knowing why it's worse is the answer that demonstrates you chose rather than defaulted.

One boundary worth naming out loud: `synchronized` only holds within a single JVM. Two app servers fronting the same station and the lock protects nothing — you'd need the slot claim as a conditional database update and let the transaction be the atom. Say it as a scope assumption and move on.








The piece you're missing is *why the database can break contention at all*, so let me start there, then show where the call goes.

**The contention breaker is that Postgres is one shared process.** Ten pods, one database. When two pods send `UPDATE slots SET state='RESERVED' WHERE id='S1' AND state='AVAILABLE'`, both statements arrive at the *same* Postgres process, which takes a row-level lock on S1 and runs them one after the other. The serialization you were getting from `synchronized` inside one JVM now happens inside Postgres on that row. The monitor didn't disappear — it moved to a place all pods can see.

Here's where it goes in the code. `depositParcel` stops being `synchronized` and becomes a transaction body:

```java
CourierDepositTicket depositParcel(Parcel parcel) {
    for (int attempt = 0; attempt < MAX_ATTEMPTS; attempt++) {
        try {
            return sqlDriver.transact(tx -> {
                // 1. read candidates
                List<SlotRow> candidates = tx.query(
                    "SELECT id, size FROM slots WHERE station_id=? AND state='AVAILABLE' AND size>=?",
                    stationId, parcel.getSize());
                if (candidates.isEmpty()) throw new NoAvailableSlotException(...);

                SlotRow chosen = bestFit(candidates);

                // 2. CLAIM — this is the contention breaker
                int rows = tx.update(
                    "UPDATE slots SET state='RESERVED' WHERE id=? AND state='AVAILABLE'",
                    chosen.id());
                if (rows == 0) throw new RetryableConflictException();  // lost the race

                // 3. claim the code; UNIQUE constraint enforces it
                tx.update("INSERT INTO tickets (id, station_id, pickup_code, slot_id, status, ...) " +
                          "VALUES (?,?,?,?, 'ACTIVE', ...)",
                          ticketId, stationId, codeGenerator.generate(), chosen.id());

                return new CourierDepositTicket(ticketId, chosen.id(), stationId, Instant.now());
            });
        } catch (RetryableConflictException | UniqueViolationException e) {
            // transaction already rolled back; loop and try again
        }
    }
    throw new NoAvailableSlotException("Could not claim a slot after " + MAX_ATTEMPTS + " attempts");
}
```

**The retry loop lives outside `transact`, not inside.** That's the part that's easy to get wrong. Once a transaction has failed you cannot keep using it — it's rolled back. You catch, then start a *fresh* transaction.

Now trace two pods hitting an empty station with only S1 free:

```
Pod A: SELECT → [S1]                 Pod B: SELECT → [S1]      ← both see it free
Pod A: UPDATE ... AND state='AVAILABLE'
       Postgres locks row S1, applies, rows=1        ← A wins
                                     Pod B: UPDATE ... AND state='AVAILABLE'
                                            blocks on A's row lock
Pod A: INSERT ticket
Pod A: COMMIT → releases lock
                                     Pod B: unblocks, re-evaluates WHERE
                                            state is now 'RESERVED' → rows=0  ← B loses
                                     Pod B: throws, ROLLBACK, retries, finds no slot
```

Both pods read S1 as free — the `SELECT` gives no protection at all, and that's fine. **The `WHERE state='AVAILABLE'` on the UPDATE is re-checked at write time, under the row lock.** That re-check is what makes it safe. `rows == 0` is Pod B being told it lost, exactly as `putIfAbsent` returning non-null told the losing thread in the single-JVM version.

Two things that follow:

**Rollback is what kills your compensation code.** If the INSERT violates the unique constraint, Postgres rolls back the whole transaction — including the slot UPDATE. The slot goes back to `AVAILABLE` with no `markFree()` call from you. The stranded-slot bug from a few messages ago can't happen, because "undo the slot claim" is no longer something you have to remember.

**This also covers multi-threading within one pod**, for free. Two threads in the same JVM open two connections; Postgres treats them exactly like two pods. So you don't need `synchronized` *and* this — the database version subsumes it. Same reason `putIfAbsent` became redundant under the lock: pick the widest-scoped mechanism and drop the narrower ones.