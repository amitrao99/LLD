Here it is in your build order, each step showing only what changed and why.

## Step 1 — Vehicle

You started here. The one decision: the enum carries the size it needs, so sizing logic never lives in an if-chain.

```java
enum VehicleType {
    BIKE(SlotSize.SMALL),
    CAR(SlotSize.MEDIUM),
    TRUCK(SlotSize.LARGE);

    private final SlotSize requiredSize;
    VehicleType(SlotSize requiredSize) { this.requiredSize = requiredSize; }
    public SlotSize requiredSize() { return requiredSize; }
}

class Vehicle {
    private final VehicleType type;
    private final String number;

    Vehicle(VehicleType type, String number) {
        this.type = type;
        this.number = number;
    }
    public VehicleType type() { return type; }
    public String number() { return number; }
}
```

## Step 2 — Slot, and the sizing rule

Explicit `rank` instead of `ordinal()`, so reordering constants can't silently break fitting. `canAccommodate` lives on the enum; `canFit` on the slot delegates to it.

```java
enum SlotSize {
    SMALL(1), MEDIUM(2), LARGE(3);

    private final int rank;
    SlotSize(int rank) { this.rank = rank; }
    public int rank() { return rank; }

    public boolean canAccommodate(SlotSize required) {
        return this.rank >= required.rank;
    }
}

enum SlotState { FREE, OCCUPIED }

class Slot {
    private final SlotSize size;
    private final int number;
    private final int floorNumber;
    private SlotState state = SlotState.FREE;

    Slot(SlotSize size, int number, int floorNumber) {
        this.size = size;
        this.number = number;
        this.floorNumber = floorNumber;
    }

    public boolean canFit(VehicleType type) {
        return size.canAccommodate(type.requiredSize());
    }
    public SlotSize size()    { return size; }
    public int number()       { return number; }
    public int floorNumber()  { return floorNumber; }
    public SlotState state()  { return state; }
    void setState(SlotState s){ this.state = s; }
}
```

**`Floor` deleted here.** Slots carry `floorNumber`; nothing in the flow needs floor-level behaviour. Reintroduce it only for per-floor display boards or per-floor locking.

## Step 3 — Money objects

`BaseRate` is the frozen terms. `PriceBreakdown` is the computed result, kept separate so the ticket never holds an amount it can't know at entry.

```java
class BaseRate {
    private final double ratePerHour;
    BaseRate(double ratePerHour) { this.ratePerHour = ratePerHour; }
    public double ratePerHour() { return ratePerHour; }
}

class PriceBreakdown {
    private final long chargeableHours;
    private final double amount;

    PriceBreakdown(long chargeableHours, double amount) {
        this.chargeableHours = chargeableHours;
        this.amount = amount;
    }
    public double amount() { return amount; }
    public long chargeableHours() { return chargeableHours; }
}
```

## Step 4 — Ticket and Receipt

Ticket is immutable and issued at entry. Exit data lives on a `Receipt`, so you never carry two null fields around.

```java
class Ticket {
    private final String id;
    private final Slot slot;
    private final Vehicle vehicle;
    private final Instant entryTime;
    private final BaseRate baseRate;   // frozen terms

    Ticket(String id, Slot slot, Vehicle vehicle, Instant entryTime, BaseRate baseRate) {
        this.id = id;
        this.slot = slot;
        this.vehicle = vehicle;
        this.entryTime = entryTime;
        this.baseRate = baseRate;
    }
    public String id()          { return id; }
    public Slot slot()          { return slot; }
    public Vehicle vehicle()    { return vehicle; }
    public Instant entryTime()  { return entryTime; }
    public BaseRate baseRate()  { return baseRate; }
}

class Receipt {
    private final Ticket ticket;
    private final Instant exitTime;
    private final PriceBreakdown breakdown;

    Receipt(Ticket ticket, Instant exitTime, PriceBreakdown breakdown) {
        this.ticket = ticket;
        this.exitTime = exitTime;
        this.breakdown = breakdown;
    }
    public PriceBreakdown breakdown() { return breakdown; }
}
```

## Step 5 — Lookup and allocation

The repository answers *what fits*; the strategy answers *which one to prefer*. That line is the important one.

```java
interface SlotRepository {
    List<Slot> findAvailable(VehicleType type);
    boolean tryOccupy(Slot slot);
    void release(Slot slot);
}

interface SlotAllocationStrategy {
    Optional<Slot> getSlotAllocation(List<Slot> availableSlots);
}

class NearestFirstStrategy implements SlotAllocationStrategy {
    public Optional<Slot> getSlotAllocation(List<Slot> available) {
        return available.stream().min(
            Comparator.comparingInt(Slot::floorNumber)
                      .thenComparingInt(Slot::number));
    }
}

class BestFitStrategy implements SlotAllocationStrategy {
    public Optional<Slot> getSlotAllocation(List<Slot> available) {
        return available.stream().min(
            Comparator.comparingInt(s -> s.size().rank()));
    }
}
```

In-memory repository — single source of truth, hands out **shared** `Slot` references (this matters for locking later):

```java
class InMemorySlotRepository implements SlotRepository {
    private final List<Slot> allSlots;
    InMemorySlotRepository(List<Slot> allSlots) { this.allSlots = allSlots; }

    public List<Slot> findAvailable(VehicleType type) {
        return allSlots.stream()
                .filter(s -> s.state() == SlotState.FREE && s.canFit(type))
                .collect(Collectors.toList());
    }
    public boolean tryOccupy(Slot slot) {
        if (slot.state() != SlotState.FREE) return false;
        slot.setState(SlotState.OCCUPIED);
        return true;
    }
    public void release(Slot slot) { slot.setState(SlotState.FREE); }
}
```

## Step 6 — Pricing

Formula lives in the strategy; numbers come off the ticket.

```java
interface PricingStrategy {
    PriceBreakdown getPriceBreakDown(BaseRate rate, Instant entry, Instant exit);
}

class HourlyPricingStrategy implements PricingStrategy {
    public PriceBreakdown getPriceBreakDown(BaseRate rate, Instant entry, Instant exit) {
        long hours = Math.max(1, (long) Math.ceil(
                Duration.between(entry, exit).toMinutes() / 60.0));
        return new PriceBreakdown(hours, hours * rate.ratePerHour());
    }
}

class PricingService {
    private final PricingStrategy strategy;
    PricingService(PricingStrategy strategy) { this.strategy = strategy; }

    public PriceBreakdown price(Ticket ticket, Instant exit) {
        return strategy.getPriceBreakDown(ticket.baseRate(), ticket.entryTime(), exit);
    }
}
```

## Step 7 — Ticket issuing and rates

```java
class TicketService {
    private final Map<String, Ticket> active = new HashMap<>();

    public Ticket generateTicket(Slot slot, Vehicle v, BaseRate rate, Instant entry) {
        Ticket t = new Ticket(UUID.randomUUID().toString(), slot, v, entry, rate);
        active.put(t.id(), t);
        return t;
    }
    public Ticket find(String id) {
        Ticket t = active.get(id);
        if (t == null) throw new IllegalArgumentException("Unknown ticket: " + id);
        return t;
    }
    public void close(String id) { active.remove(id); }
}

class RateProvider {
    private final Map<VehicleType, BaseRate> rates;
    RateProvider(Map<VehicleType, BaseRate> rates) { this.rates = rates; }
    public BaseRate rateFor(VehicleType type) { return rates.get(type); }
}
```

## Step 8 — The orchestrator (single-threaded)

```java
class ParkingService {
    private final SlotRepository slots;
    private final SlotAllocationStrategy allocation;
    private final TicketService tickets;
    private final PricingService pricing;
    private final RateProvider rates;

    ParkingService(SlotRepository slots, SlotAllocationStrategy allocation,
                   TicketService tickets, PricingService pricing, RateProvider rates) {
        this.slots = slots; this.allocation = allocation;
        this.tickets = tickets; this.pricing = pricing; this.rates = rates;
    }

    public Ticket park(Vehicle vehicle) {
        List<Slot> candidates = slots.findAvailable(vehicle.type());
        Slot chosen = allocation.getSlotAllocation(candidates)
                                .orElseThrow(LotFullException::new);
        slots.tryOccupy(chosen);
        return tickets.generateTicket(chosen, vehicle,
                                      rates.rateFor(vehicle.type()), Instant.now());
    }

    public Receipt unpark(String ticketId) {
        Ticket ticket = tickets.find(ticketId);
        Instant exit = Instant.now();
        PriceBreakdown breakdown = pricing.price(ticket, exit);
        slots.release(ticket.slot());
        tickets.close(ticketId);
        return new Receipt(ticket, exit, breakdown);
    }
}

class LotFullException extends RuntimeException {
    LotFullException() { super("No slot available"); }
}
```

That's the complete baseline — this is what you lay down in the first 10–12 minutes.

## Add-on — multiple gates / concurrency

Only two things change. **`park` becomes a drain loop**, and **`tryOccupy` becomes atomic**. Nothing else in the design moves, which is the payoff for keeping allocation pure.

```java
public Ticket park(Vehicle vehicle) {
    // Eligibility: no lock. Snapshot, may go stale — that's acceptable.
    List<Slot> candidates = new ArrayList<>(slots.findAvailable(vehicle.type()));
    if (candidates.isEmpty()) throw new LotFullException();

    while (!candidates.isEmpty()) {
        Slot chosen = allocation.getSlotAllocation(candidates)
                                .orElseThrow(LotFullException::new);

        if (!slots.tryOccupy(chosen)) {   // atomic claim; lost the race
            candidates.remove(chosen);
            continue;
        }

        try {
            return tickets.generateTicket(chosen, vehicle,
                                          rates.rateFor(vehicle.type()), Instant.now());
        } catch (RuntimeException e) {
            slots.release(chosen);        // never leak an occupied slot
            throw e;
        }
    }
    throw new LotFullException();         // every candidate was claimed under us
}
```

And the repository's claim, with the recheck **inside** the lock:

```java
public boolean tryOccupy(Slot slot) {
    synchronized (slot) {                          // per-slot lock
        if (slot.state() != SlotState.FREE) return false;
        slot.setState(SlotState.OCCUPIED);
        return true;
    }
}
public void release(Slot slot) {
    synchronized (slot) { slot.setState(SlotState.FREE); }
}
```

The four points to say out loud when you write this:

- **Per-slot lock, not per-service** — two cars claiming different slots never block each other.
- **Terminates without a magic retry count** — each iteration returns or removes an element.
- **Ticket generation sits outside the lock** — critical section is one state check and one write.
- **Claim and ticket-issue aren't atomic together** — the catch patches it in memory; a real system puts both in one transaction.

That's the whole thing, roughly 200 lines. You've designed it thoroughly — the remaining gap is producing it cold in 25 minutes, and that's a different muscle. Say go and I'll start the clock.