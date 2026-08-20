Yes — your thinking is **correct**, and for a **30-minute LLD / ~20-minute coding round**, this is exactly the right level of scoping.

The main thing I would change is just the way you **structure and verbalize it**, so you don't spend too much interview time exploring dimensions that you aren't going to implement.

For this round, I would think about Rate Limiter in this order:

1. **What is being limited?**
2. **What operation does my system expose?**
3. **What algorithm/policy decides allow vs deny?**
4. **What state do I maintain per user?**
5. **How do I keep the design extensible without overengineering it?**
6. Then immediately code.

For your current thought:

> "A rate limiter limits on what?"

That's a **good first question**.

You can say something like:

> "I'll scope the initial implementation to per-user rate limiting. Every request has a user identifier, and the rate limiter decides whether that user's request should be allowed or rejected."

Perfect. Don't immediately go into API-level limits, IP limits, resource limits, tenant limits, etc. You can mention:

> "The key could later be generalized from userId to some rate-limit key, but I'll use userId for this implementation."

That's enough.

---

### Your core abstraction is also right

Conceptually:

```text
Client
  |
  v
RateLimiter
  |
  | allow?
  |
  +---- yes ----> Actual Resource
  |
  +---- no -----> Reject
```

The rate limiter itself does **not need to know what the downstream resource is**.

Its responsibility is simply:

```java
boolean allowRequest(String userId);
```

I would prefer `allowRequest()` over `check()` because `check()` is slightly vague.

So your first interface can literally be:

```java
interface RateLimiter {
    boolean allowRequest(String userId);
}
```

That's already a very good interview starting point.

---

Now there's one important design decision immediately after this.

You need to separate:

**Who is asking?**

from

**How do I decide whether they are allowed?**

The `userId` answers the first question.

The **rate limiting algorithm** answers the second.

For example:

```text
Fixed Window
Sliding Window
Token Bucket
Leaky Bucket
```

For a 20-minute coding round, I would **not** try to support all four.

Instead say:

> "There are multiple rate-limiting policies. I'll make the design extensible at the policy level, but implement one algorithm completely."

That gives you good LLD signals without destroying your coding time.

---

## The cleanest 30-minute structure

I'd probably steer toward this:

```text
             RateLimiter
                 |
                 v
        RateLimitPolicy
                 |
        -------------------
        |                 |
   TokenBucket       FixedWindow
   (implement)       (future)
```

But even this can be simplified further.

For the interview, you may simply have:

```java
interface RateLimiter {
    boolean allowRequest(String userId);
}
```

and:

```java
class TokenBucketRateLimiter implements RateLimiter {
    ...
}
```

That's absolutely enough unless the interviewer explicitly asks for multiple algorithms.

---

### Then your state becomes the important part

If you're limiting **per user**, then each user needs independent state.

For token bucket, for example:

```text
user1 -> Bucket
user2 -> Bucket
user3 -> Bucket
```

Therefore naturally:

```java
Map<String, TokenBucket> buckets;
```

And the `TokenBucket` contains something like:

```java
class TokenBucket {
    private double tokens;
    private long lastRefillTime;
}
```

The configuration can live in the limiter:

```java
capacity
refillRate
```

So now mentally your design is already almost complete:

```text
TokenBucketRateLimiter

- capacity
- refillRate
- Map<userId, TokenBucket>

+ allowRequest(userId)
```

That's the kind of design you can actually implement in 15–20 minutes.

---

## One thing I'd slightly correct in your wording

You said:

> "someone asks the rate limiter to either let the request pass, go to the actual resource, or deny it"

Conceptually yes, but in **your implementation**, I wouldn't make the RateLimiter responsible for forwarding the request.

Don't build:

```java
rateLimiter.process(request, resource);
```

because then it starts becoming middleware / proxy / gateway logic.

Keep it much cleaner:

```java
if (rateLimiter.allowRequest(userId)) {
    // caller invokes resource
} else {
    // caller rejects request
}
```

So the RateLimiter's **single responsibility** is:

> Make the admission decision.

That is a nice thing to explicitly tell the interviewer.

---

## So your first 2–3 minutes should sound roughly like this

You don't need to memorize the wording, but the thinking should be:

> "I'll first scope what we're rate limiting. I'll assume requests are rate-limited per user, identified by userId. The rate limiter's responsibility is only to determine whether a request is allowed; actually forwarding the request is outside its responsibility.
>
> I'll expose a simple `allowRequest(userId)` API. There are several algorithms like fixed window, sliding window and token bucket. I'll keep the design open to supporting different strategies, but implement one completely — probably token bucket."

And then **stop discussing requirements and start designing**.

For your interview constraints, that is a very strong start.

The progression in your head should basically be:

```text
WHAT?
Per-user request limiting

API?
allowRequest(userId)

WHO MAKES THE DECISION?
RateLimiter

WHICH POLICY?
Token Bucket

WHAT STATE?
Bucket per user

WHERE?
Map<userId, Bucket>

CONCURRENCY?
Handle during allowRequest()

EXTENSIBILITY?
Another RateLimiter implementation
```

That's enough. You do **not** need distributed Redis rate limiting, multiple servers, persistence, cleanup jobs, API gateways, HTTP 429 handling, configuration services, metrics, etc. unless the interviewer pushes you there.

For this exact **20-minute Java coding scope**, I'd actually keep the final design to around **3 classes/interfaces maximum initially**: `RateLimiter`, `TokenBucketRateLimiter`, and `TokenBucket`. Then we can layer concurrency and extensibility onto that without making the code explode.





Yes, that is the right direction. For your interview scope, I would keep the time handling **very simple** and use milliseconds consistently.

I’d slightly adjust one part: you do **not** create one `Instant` when the rate limiter is created and reuse it. Each bucket stores the **last time it was refilled**, and every incoming request gets the **current time**.

So conceptually:

```java
long now = System.currentTimeMillis();
long elapsedMillis = now - bucket.getLastRefillTime();
```

Then your refill calculation is:

```text
tokensToAdd = elapsedTime × refillRate
```

The only question is: **what are the units of `refillRate`?**

For simplicity, define:

```java
double refillRatePerSecond;
```

Example:

```text
capacity = 10 tokens
refillRate = 2 tokens/second
```

Suppose:

```text
lastRefillTime = 1000 ms
currentTime    = 2500 ms
```

Elapsed:

```text
1500 ms = 1.5 seconds
```

So:

```text
tokensToAdd = 1.5 × 2
            = 3 tokens
```

In code:

```java
double elapsedSeconds = (now - lastRefillTime) / 1000.0;

double tokensToAdd = elapsedSeconds * refillRatePerSecond;

tokens = Math.min(capacity, tokens + tokensToAdd);

lastRefillTime = now;
```

That is probably the **cleanest calculation to remember**.

---

And notice that this naturally leads to using:

```java
double tokens;
```

rather than:

```java
int tokens;
```

because after 250 ms at 2 tokens/sec you have earned:

```text
0.5 token
```

You can accumulate that fractional token internally.

A request costs:

```java
1 token
```

So:

```java
if (tokens >= 1.0) {
    tokens -= 1.0;
    return true;
}

return false;
```

That's the entire token-bucket mathematics.

---

### `Instant` vs `System.currentTimeMillis()`

Your `Instant` thought is valid:

```java
Instant now = Instant.now();

long elapsedMillis =
        Duration.between(lastRefillTime, now).toMillis();
```

where:

```java
private Instant lastRefillTime;
```

But for a **20-minute Java LLD round**, I would personally use:

```java
long lastRefillTimeMillis;
```

and:

```java
System.currentTimeMillis();
```

because there's less ceremony.

You can tell the interviewer:

> "I'm keeping time in milliseconds for simplicity. In production I could inject a Clock for testability."

That's enough. You don't actually need to implement `Clock` unless they ask.

---

So your bucket becomes extremely concrete:

```java
class TokenBucket {

    private double tokens;
    private long lastRefillTimeMillis;

    public TokenBucket(int capacity) {
        this.tokens = capacity;
        this.lastRefillTimeMillis = System.currentTimeMillis();
    }
}
```

Then on **every request**:

```text
1. Get current time.
2. Calculate elapsed time.
3. Refill based on elapsed time.
4. Cap tokens at capacity.
5. Update lastRefillTime.
6. If >= 1 token:
      consume 1
      allow
   else:
      deny
```

That's all you need to remember.

One subtle point: **you do not need a background refill thread.** Tokens are refilled lazily when a request arrives.

For example, if nobody calls the rate limiter for 10 minutes, nothing happens. When the next request arrives, you calculate that 10 minutes have elapsed and refill the bucket appropriately.

That is much simpler and exactly what I'd implement in your round.




Yes — start the bucket **full at capacity**, and set `lastRefillTime = Instant.now()` in the constructor.

On the integer-vs-double question: for your interview, **integer tokens are actually simpler**, but you need to be careful not to lose partial elapsed time.

Say:

```java
int capacity;
int tokens;
int refillRatePerSecond;
Instant lastRefillTime;
```

Then on a request:

```java
Instant now = Instant.now();

long elapsedMillis =
        Duration.between(lastRefillTime, now).toMillis();

int tokensGained =
        (int) ((elapsedMillis * refillRatePerSecond) / 1000);
```

Then:

```java
tokens = Math.min(capacity, tokens + tokensGained);
```

But here's the subtle part: **don't blindly do**:

```java
lastRefillTime = now;
```

if `tokensGained == 0`.

Example: refill rate = 1 token/sec.

```text
Request at 600 ms  → gained 0 → if you reset time
Request at 1200 ms → only 600 ms seen again → gained 0
```

You could theoretically keep getting requests and never gain a token.

### Simplest correct integer approach

Only advance the refill timestamp by the amount of time you actually converted into tokens.

Suppose:

```java
int tokensGained =
    (int) ((elapsedMillis * refillRatePerSecond) / 1000);
```

For a **simple interview version**, if you define the refill as something easy like:

> 1 token every N milliseconds

it becomes even cleaner.

For example:

```java
long refillIntervalMillis = 1000; // 1 token every second
```

Then:

```java
long elapsedMillis =
        Duration.between(lastRefillTime, now).toMillis();

int tokensGained =
        (int) (elapsedMillis / refillIntervalMillis);
```

And:

```java
if (tokensGained > 0) {
    tokens = Math.min(capacity, tokens + tokensGained);

    lastRefillTime =
        lastRefillTime.plusMillis(
            tokensGained * refillIntervalMillis
        );
}
```

This preserves the leftover fractional time.

So if:

```text
last refill = 0 ms
now         = 1500 ms
interval    = 1000 ms
```

you gain:

```text
1 token
```

and move `lastRefillTime` to:

```text
1000 ms
```

**not 1500 ms.**

The extra 500 ms remains available toward the next token.

---

For your **20-minute coding round**, I'd choose this formulation:

```java
private int capacity;
private int tokens;
private long refillIntervalMillis;
private Instant lastRefillTime;
```

Constructor:

```java
this.capacity = capacity;
this.tokens = capacity;
this.refillIntervalMillis = refillIntervalMillis;
this.lastRefillTime = Instant.now();
```

Then mentally the algorithm is simply:

```text
elapsed time
    ↓
elapsed / refill interval
    ↓
integer tokens gained
    ↓
min(capacity, current + gained)
    ↓
advance lastRefillTime only by consumed intervals
    ↓
if token exists → consume → true
else → false
```

I actually prefer this over `double` **for your particular interview**. It's easier to explain, easier to debug on a whiteboard/editor, and avoids floating-point discussion entirely. The only assumption you're making is that tokens refill in discrete units, which is perfectly reasonable for the scoped implementation.







Yes — **that is a perfectly acceptable approach**, with one caveat: preserve the fractional elapsed time, otherwise you can lose refill progress.

You can say:

```java
double refillRatePerSecond;
int tokens;
Instant lastRefillTime;
```

Then:

```java
Instant now = Instant.now();

double elapsedSeconds =
        Duration.between(lastRefillTime, now).toMillis() / 1000.0;

int tokensGained =
        (int) (elapsedSeconds * refillRatePerSecond);
```

Then:

```java
tokens = Math.min(capacity, tokens + tokensGained);
```

The cast to `int` simply means:

> Only complete tokens are usable.

So if:

```text
elapsedSeconds = 1.5
refillRate = 2 tokens/sec

tokensGained = (int)(1.5 * 2)
             = 3
```

Perfect.

But if:

```text
elapsedSeconds = 0.6
refillRate = 1 token/sec
```

then:

```text
tokensGained = (int) 0.6 = 0
```

So you should **not set `lastRefillTime = now` unconditionally**, because you'd throw away that 0.6 seconds.

For your round, you have two reasonable choices:

**Simplest:** keep `tokens` as a `double`. Then you can safely update `lastRefillTime = now` every time.

```java
double tokensToAdd = elapsedSeconds * refillRatePerSecond;

tokens = Math.min(capacity, tokens + tokensToAdd);
lastRefillTime = now;
```

Then consume if:

```java
if (tokens >= 1.0) {
    tokens -= 1.0;
    return true;
}
```

This is actually the version I'd now recommend. The arithmetic is not really complicated, and it eliminates the leftover-time bookkeeping entirely.

So your state becomes:

```java
int capacity;
double tokens;
double refillRatePerSecond;
Instant lastRefillTime;
```

That's clean, correct, and very easy to explain:

> "Internally I allow fractional tokens to accumulate. A request requires one complete token."

For a 20-minute LLD coding round, that's probably the sweet spot.




Yes. Given your scope, I would structure it exactly as a **RateLimiter class delegating to a rate-limiting strategy**, and implement only Token Bucket.

### 1. Interfaces / classes involved

```text
1. RateLimitingStrategy          // interface
   + boolean allowRequest(String userId)

2. TokenBucketRateLimitingStrategy
   implements RateLimitingStrategy

3. TokenBucket                  // state for one user

4. RateLimiter                  // entry point used by caller
   - RateLimitingStrategy strategy
   + boolean allowRequest(String userId)

5. Main                         // driver/demo
```

**Enums:** None required.

The relationship is:

```text
Client
   |
   v
RateLimiter
   |
   v
RateLimitingStrategy
   |
   v
TokenBucketRateLimitingStrategy
   |
   v
Map<String, TokenBucket>
```

That is enough abstraction for a 20-minute implementation.

---

## 2. Complete Java code

```java
import java.time.Duration;
import java.time.Instant;
import java.util.HashMap;
import java.util.Map;


// Strategy interface.
// Any rate limiting algorithm should implement this.
interface RateLimitingStrategy {

    boolean allowRequest(String userId);
}


// Represents the token bucket belonging to one user.
class TokenBucket {

    private final int capacity;

    // Double allows fractional tokens to accumulate.
    private double tokens;

    private Instant lastRefillTime;


    public TokenBucket(int capacity) {

        this.capacity = capacity;

        // Bucket starts completely full.
        this.tokens = capacity;

        this.lastRefillTime = Instant.now();
    }


    public int getCapacity() {
        return capacity;
    }


    public double getTokens() {
        return tokens;
    }


    public void setTokens(double tokens) {
        this.tokens = tokens;
    }


    public Instant getLastRefillTime() {
        return lastRefillTime;
    }


    public void setLastRefillTime(Instant lastRefillTime) {
        this.lastRefillTime = lastRefillTime;
    }
}


// Token Bucket implementation of the strategy.
class TokenBucketRateLimitingStrategy implements RateLimitingStrategy {

    // Maximum number of tokens each user's bucket can hold.
    private final int capacity;

    // Number of tokens generated every second.
    private final double refillRatePerSecond;

    // Each user gets an independent token bucket.
    private final Map<String, TokenBucket> buckets;


    public TokenBucketRateLimitingStrategy(
            int capacity,
            double refillRatePerSecond) {

        this.capacity = capacity;
        this.refillRatePerSecond = refillRatePerSecond;

        this.buckets = new HashMap<>();
    }


    @Override
    public boolean allowRequest(String userId) {

        // Create the user's bucket when we see the user
        // for the first time.
        TokenBucket bucket = buckets.get(userId);

        if (bucket == null) {

            bucket = new TokenBucket(capacity);

            buckets.put(userId, bucket);
        }


        // First refill the bucket based on elapsed time.
        refill(bucket);


        // One request consumes one complete token.
        if (bucket.getTokens() >= 1.0) {

            bucket.setTokens(
                    bucket.getTokens() - 1.0
            );

            return true;
        }


        // No complete token is available.
        return false;
    }


    private void refill(TokenBucket bucket) {

        Instant now = Instant.now();


        // Find how much time has passed since
        // the previous refill calculation.
        long elapsedMillis =
                Duration.between(
                        bucket.getLastRefillTime(),
                        now
                ).toMillis();


        // Convert milliseconds to seconds.
        double elapsedSeconds =
                elapsedMillis / 1000.0;


        // Calculate fractional tokens earned.
        double tokensToAdd =
                elapsedSeconds * refillRatePerSecond;


        // Never exceed bucket capacity.
        double updatedTokens =
                Math.min(
                        bucket.getCapacity(),
                        bucket.getTokens() + tokensToAdd
                );


        bucket.setTokens(updatedTokens);


        // Because we preserve fractional tokens,
        // it is safe to move the timestamp to now.
        bucket.setLastRefillTime(now);
    }
}


// Main RateLimiter exposed to the caller.
class RateLimiter {

    private final RateLimitingStrategy strategy;


    public RateLimiter(RateLimitingStrategy strategy) {

        this.strategy = strategy;
    }


    public boolean allowRequest(String userId) {

        return strategy.allowRequest(userId);
    }
}


// Simple driver code.
public class Main {

    public static void main(String[] args)
            throws InterruptedException {

        // Capacity = 3 requests.
        // Refill = 1 token every second.
        RateLimitingStrategy strategy =
                new TokenBucketRateLimitingStrategy(
                        3,
                        1.0
                );


        RateLimiter rateLimiter =
                new RateLimiter(strategy);


        String userId = "user-1";


        // First three requests should pass
        // because bucket starts full.
        System.out.println(
                rateLimiter.allowRequest(userId)
        ); // true

        System.out.println(
                rateLimiter.allowRequest(userId)
        ); // true

        System.out.println(
                rateLimiter.allowRequest(userId)
        ); // true


        // Bucket is empty.
        System.out.println(
                rateLimiter.allowRequest(userId)
        ); // false


        // Wait long enough to generate approximately one token.
        Thread.sleep(1100);


        System.out.println(
                rateLimiter.allowRequest(userId)
        ); // true
    }
}
```

### The mental model I want you to carry into the interview

Don't memorize all that code. Memorize this flow:

```text
allowRequest(userId)

      ↓

get/create user's bucket

      ↓

refill(bucket)

elapsed = now - lastRefill
tokensToAdd = elapsedSeconds × refillRate

tokens =
    min(capacity, tokens + tokensToAdd)

lastRefill = now

      ↓

tokens >= 1?

 YES               NO
  |                  |
tokens--            false
  |
 true
```

There is one thing I'd expect the interviewer to push on almost immediately: **concurrency**.

Right now:

```java
HashMap<String, TokenBucket>
```

and this sequence:

```java
refill(bucket);
if (bucket.getTokens() >= 1) {
    bucket.setTokens(bucket.getTokens() - 1);
}
```

are **not thread-safe**.

But I would **not solve that preemptively in your first version**. Write this clean version first. If the interviewer asks, *"What happens if two requests for the same user arrive simultaneously?"*, that's where we add synchronization in a very small change rather than complicating the base design.




Exactly — this is the concurrency hole.

If two requests for the **same new user** arrive at the same time, this is unsafe:

```java
TokenBucket bucket = buckets.get(userId);

if (bucket == null) {
    bucket = new TokenBucket(capacity);
    buckets.put(userId, bucket);
}
```

Both threads can see `null`, both create separate buckets, and both may proceed using different bucket objects.

For your interview scope, the cleanest fix is:

```java
ConcurrentHashMap<String, TokenBucket> buckets;
```

and then:

```java
TokenBucket bucket =
        buckets.computeIfAbsent(
                userId,
                id -> new TokenBucket(capacity)
        );
```

`computeIfAbsent` gives you the important property you want here: for that key, you safely obtain the bucket associated with the user instead of doing the unsafe separate `get()` + `put()` sequence.

Then **after obtaining the bucket**, synchronize on that bucket:

```java
@Override
public boolean allowRequest(String userId) {

    TokenBucket bucket =
            buckets.computeIfAbsent(
                    userId,
                    id -> new TokenBucket(capacity)
            );

    synchronized (bucket) {

        refill(bucket);

        if (bucket.getTokens() >= 1.0) {
            bucket.setTokens(bucket.getTokens() - 1.0);
            return true;
        }

        return false;
    }
}
```

So there are really **two separate concurrency problems**, and this is a nice interview point:

```text
Problem 1:
Safely create/get one bucket per user
→ ConcurrentHashMap + computeIfAbsent()

Problem 2:
Safely modify one user's bucket
→ synchronized(bucket)
```

And importantly, you're **not** doing:

```java
synchronized (this)
```

or synchronizing the entire `allowRequest()` method, because then:

```text
user A request
user B request
user C request
```

would unnecessarily block each other.

With:

```java
synchronized (bucket)
```

only requests belonging to the **same user** contend with each other.

So:

```text
Thread 1 → user A bucket ─┐
                          ├─ serialized
Thread 2 → user A bucket ─┘

Thread 3 → user B bucket ─── can proceed independently
```

For your 30-minute LLD round, I would stop right there. `ConcurrentHashMap + computeIfAbsent + synchronized(bucket)` is simple, concrete, and gives you a strong concurrency story without introducing locks, atomics, or complicated concurrent state management.




Yes. For a `ConcurrentHashMap`, `computeIfAbsent()` handles this case atomically **for that key**. So if two threads arrive for the same missing `userId`, you do not end up installing two different buckets in the map.

Think of it like this:

```text
Map initially:

"userA" -> ABSENT
```

Two requests arrive:

```text
Thread T1                           Thread T2
    |                                   |
    | computeIfAbsent("userA")          | computeIfAbsent("userA")
    |                                   |
    +----------------+------------------+
                     |
             ConcurrentHashMap
             coordinates access
                     |
              Is "userA" present?
                     |
                    NO
                     |
            One thread gets to
            create the value
                     |
              T1 creates Bucket B
                     |
          map["userA"] = Bucket B
                     |
              +------+------+
              |             |
              v             v
        T1 receives B   T2 receives B
              |             |
              +------+------+
                     |
          Both now reference the
             SAME TokenBucket
```

Then your code continues:

```java
TokenBucket bucket =
        buckets.computeIfAbsent(
                userId,
                id -> new TokenBucket(capacity)
        );

synchronized (bucket) {
    ...
}
```

Now imagine T1 and T2 both reach `synchronized(bucket)`:

```text
              Both have Bucket B
                     |
            +--------+--------+
            |                 |
           T1                T2
            |                 |
            v                 v
     synchronized(B)    synchronized(B)
            |                 |
      acquires lock        waits
            |
        refill()
            |
      check token
            |
      consume token
            |
       exits lock
            |
            +-------------------->
                                  |
                            T2 acquires lock
                                  |
                              refill()
                                  |
                            check token
                                  |
                            consume/deny
                                  |
                              exits lock
```

So there are **two layers of protection**:

```text
ConcurrentHashMap.computeIfAbsent()
        |
        | solves
        v
"Make sure we safely obtain the bucket for this user"

synchronized(bucket)
        |
        | solves
        v
"Make sure two requests don't modify that bucket simultaneously"
```

### One nuance worth knowing

I would phrase `computeIfAbsent` carefully in an interview. Don't say:

> "Java guarantees the lambda can physically execute only once under every imaginable circumstance."

The important guarantee for your design is that the map operation is atomic for the key and you safely end up using the bucket associated with that key.

So your interview explanation can simply be:

> "I'll use `ConcurrentHashMap.computeIfAbsent()` so concurrent first requests safely initialize or obtain the per-user bucket. Once I have that shared bucket, I'll synchronize on the bucket itself while refilling and consuming tokens."

That is more than sufficient for this LLD round.



Yes. For your **30-minute LLD scope**, the most natural extensions are:

* **Other rate-limiting strategies**

  * Fixed Window Counter
  * Sliding Window Log
  * Sliding Window Counter
  * Leaky Bucket
  * Token Bucket — current implementation

Because you already have:

```java
interface RateLimitingStrategy {
    boolean allowRequest(String userId);
}
```

these become alternate implementations.

Beyond strategy implementations, the other extensions I would expect an interviewer to ask about are:

1. **Different rate-limit keys**
   Right now you limit by `userId`. Later this could be:

   ```text
   user
   IP address
   API key
   tenant
   endpoint
   user + endpoint
   ```

   Instead of hardcoding `userId`, you could eventually use a generic `key`.

2. **Different limits for different users/plans**
   Example:

   ```text
   FREE      -> 10 req/sec
   PREMIUM   -> 100 req/sec
   INTERNAL  -> 1000 req/sec
   ```

   Then capacity/refill rate come from some configuration rather than being globally fixed.

3. **Different limits per resource/API**
   Example:

   ```text
   userA + /search   -> 10/sec
   userA + /upload   -> 2/sec
   ```

   Your map key could become something like:

   ```java
   userId + ":" + resourceId
   ```

4. **Thread safety**
   You've already handled the natural single-process version:

   ```java
   ConcurrentHashMap
   + computeIfAbsent
   + synchronized(bucket)
   ```

5. **Distributed rate limiting**
   This is probably the biggest follow-up:

   ```text
                Load Balancer

              /      |      \
             /       |       \
          Server1 Server2 Server3
   ```

   Your in-memory map no longer works globally because each server has its own buckets.

   Then you'd say:

   > "For a distributed deployment, I'd move shared rate-limit state to something like Redis and perform refill-and-consume atomically."

   You don't need to code this in the LLD round unless explicitly asked.

6. **Bucket cleanup / memory growth**
   Your map currently grows forever:

   ```java
   Map<String, TokenBucket>
   ```

   If millions of users appear once, stale buckets remain.

   An extension is TTL/eviction:

   > "Inactive buckets can be periodically removed after some idle period."

7. **Request cost / weighted tokens**
   Currently:

   ```text
   one request = one token
   ```

   Could become:

   ```text
   GET profile   = 1 token
   expensive API = 5 tokens
   bulk export   = 20 tokens
   ```

   So:

   ```java
   allowRequest(String userId, int tokensRequired)
   ```

8. **Observability**
   Track:

   ```text
   allowed requests
   rejected requests
   current utilization
   rate-limit hits
   ```

   But just mention this; don't build metrics classes in a 20-minute implementation.

The interviewer hierarchy I'd keep in your head is:

```text
Most likely extensions

1. Another algorithm
2. Per-user/per-API configuration
3. Concurrency
4. Distributed rate limiter
5. Cleanup/eviction
6. Weighted requests
```

And if they say, **"How would you extend this?"**, don't start coding everything.

I'd answer:

> "The strategy abstraction already lets me add Fixed Window, Sliding Window, or Leaky Bucket without changing `RateLimiter`. Beyond algorithm choice, I can generalize the key from just userId to user/API/tenant combinations, support different configurations per key, add eviction for inactive buckets, and for a distributed deployment move the state to Redis with atomic updates."

That's a very strong 30-second LLD answer.


Yes. Your intuition is mostly right. For your interview, I’d remember them as **three different ways of maintaining “recent request pressure.”**

### Fixed Window

**One-liner:** Divide time into fixed blocks and allow at most `N` requests inside each block.

Example: `100 requests / 60 seconds`.

```text
12:00:00 -------- 12:00:59   counter = 0..100
12:01:00 -------- 12:01:59   counter resets
```

You don't really need to start chunking from when the object was created. You can just maintain:

```text
windowStart
requestCount
windowDuration
limit
```

Pseudocode:

```java
allowRequest(userId):

    window = getOrCreateWindow(userId)

    now = Instant.now()

    if duration(window.windowStart, now) >= windowDuration:
        window.windowStart = now
        window.requestCount = 0

    if window.requestCount >= limit:
        return false

    window.requestCount++
    return true
```

Very easy to implement.

The weakness is the **boundary burst problem**.

Suppose limit = 100/minute:

```text
12:00:59 → 100 requests
12:01:00 → 100 requests
```

You effectively allowed 200 requests within roughly one second.

---

### Sliding Window Log

**One-liner:** Keep the timestamps of actual recent requests and count only those inside the immediately preceding time window.

This is probably the easiest sliding-window version to understand.

For every user:

```java
Deque<Instant> requestTimes;
```

Suppose the rule is:

```text
3 requests per 10 seconds
```

At time `15s`, you care about:

```text
5s ---------------- 15s
         ↑
      only timestamps
      inside here matter
```

Pseudocode:

```java
allowRequest(userId):

    queue = getOrCreateQueue(userId)

    now = Instant.now()
    cutoff = now - windowDuration

    while queue is not empty
          AND queue.front <= cutoff:

        queue.removeFirst()

    if queue.size() >= limit:
        return false

    queue.addLast(now)

    return true
```

That's it.

So unlike Fixed Window:

```text
Fixed:
"Which bucket of time am I currently in?"

Sliding:
"How many requests happened during the last X seconds from RIGHT NOW?"
```

This gives more accurate rate limiting, but you're storing timestamps, so memory usage is higher.

For an LLD interview, if someone says **"implement sliding window"**, this is probably the version I'd code because it is extremely understandable.

---

### Sliding Window Counter

There's another optimized sliding-window algorithm. I would **mention it but probably not code it** in your round unless specifically requested.

Instead of storing every timestamp, maintain:

```text
previousWindowCount
currentWindowCount
```

Then estimate how much of the previous window overlaps with the current sliding window.

Conceptually:

```text
effectiveCount =
    currentWindowCount
    +
    previousWindowCount × overlapPercentage
```

Example:

```text
Previous minute: 80 requests
Current minute: 20 requests

We're 25% into current minute.

75% of previous window still overlaps.

Estimated requests =
    20 + (80 × 0.75)
    = 80
```

More memory-efficient than keeping every timestamp, but more arithmetic and approximate.

For your interview:

> Sliding Window Log = exact + simpler code
> Sliding Window Counter = approximate + more memory-efficient

---

## Leaky Bucket

Your understanding needs one small adjustment.

You said:

> "It keeps accumulating till the threshold and allows requests at a steady state."

Almost.

The conceptual model is literally a bucket with a hole:

```text
Incoming Requests
       ↓ ↓ ↓ ↓ ↓
   +-----------+
   | requests  |
   | requests  |
   | requests  |   ← finite capacity
   +-----+-----+
         |
         | fixed leak rate
         ↓
      Processing
```

Requests can arrive in bursts, but they **leave/process at a constant rate**.

If the bucket/queue becomes full:

```text
new request → rejected
```

So state can conceptually be:

```text
capacity
queue
leakRate
```

The "true" version could use a worker/timer:

```java
onRequest(request):

    if queue.size() == capacity:
        reject

    queue.add(request)
```

And separately:

```java
worker:

    every 100ms:

        if queue not empty:
            request = queue.remove()
            process(request)
```

But you're absolutely right: **that introduces a streaming/background-worker nature**, which is more annoying in a 20-minute LLD round.

---

There is also a simpler mathematical implementation where you don't actually run a background thread.

Maintain:

```text
currentWaterLevel
lastLeakTime
capacity
leakRatePerSecond
```

When a request arrives:

```java
allowRequest():

    now = Instant.now()

    elapsedSeconds =
        duration(lastLeakTime, now)

    leaked =
        elapsedSeconds * leakRatePerSecond

    waterLevel =
        max(0, waterLevel - leaked)

    lastLeakTime = now

    if waterLevel + 1 > capacity:
        return false

    waterLevel += 1

    return true
```

Notice how similar this is to Token Bucket.

Token bucket:

```text
time passes
    ↓
tokens INCREASE
    ↓
request consumes token
```

Leaky bucket:

```text
time passes
    ↓
water level DECREASES
    ↓
request adds water
```

They're almost mathematical opposites.

But there is an important conceptual distinction:

**Token Bucket**

```text
Tokens accumulate while idle
        ↓
Later you can allow a burst
```

**Leaky Bucket**

```text
Requests accumulate
        ↓
Output is smoothed to a fixed rate
```

That distinction is probably the one the interviewer cares about.

### The four algorithms I'd memorize

```text
FIXED WINDOW
State: counter + windowStart
Idea: N requests per fixed time block
Pros: simplest
Problem: boundary bursts


SLIDING WINDOW LOG
State: Deque<timestamp>
Idea: keep timestamps from last X seconds
Pros: accurate
Problem: more memory


TOKEN BUCKET
State: tokens + lastRefillTime
Idea: tokens regenerate; request consumes one
Pros: permits controlled bursts
Problem: slightly more arithmetic


LEAKY BUCKET
State: queue/waterLevel + lastLeakTime
Idea: requests enter quickly but leave steadily
Pros: smooth output rate
Problem: buffering/queueing is more involved
```

And for **your 20-minute coding round**, my coding difficulty ranking would be:

```text
Fixed Window             ★
Token Bucket              ★★
Sliding Window Log        ★★
Leaky Bucket              ★★★
Sliding Window Counter    ★★★
```

So if the interviewer says, "Pick an algorithm and implement it," **Token Bucket is still a very good choice**: enough design substance to discuss refill/time/concurrency, but still compact enough to finish.
