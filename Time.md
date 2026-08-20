```java
Instant start = Instant.now();
Instant end   = Instant.now();
Duration d    = Duration.between(start, end);   // start → end
long mins     = d.toMinutes();                  // toSeconds, toMillis, toHours
Instant expiry = start.plus(Duration.ofMinutes(30));  // or start.plusSeconds(1800)
boolean expired = Instant.now().isAfter(expiry);
```

That covers parking lot fees, cache TTL, rate limiter windows, session expiry, ride duration, elevator timing, audit logs, ordering events. `Instant` is comparable and has `isBefore`/`isAfter`, so sorting and expiry checks are free.

**The one extra thing worth remembering:** inject a `Clock` instead of calling `Instant.now()` statically.

```java
class ParkingLot {
    private final Clock clock;
    ParkingLot(Clock clock) { this.clock = clock; }
    void exit(Ticket t) {
        Duration d = Duration.between(t.getEntry(), Instant.now(clock));
        ...
    }
}
// prod: Clock.systemUTC()   test: Clock.fixed(someInstant, ZoneOffset.UTC)
```

Interviewers love this because it makes time testable, and it costs you one field. It's the single highest-value time detail you can drop in an LLD round.


```java
long ms = Instant.now().toEpochMilli();
```

```java
Duration d = Duration.between(start, end);
d.toNanos();     // total nanos   (overflows past ~292 years — fine for you)
d.toMillis();    // total millis
d.toSeconds();   // total seconds
d.toMinutes();   // total minutes
```

## One trap worth knowing

`Instant.now()` is wall-clock time, and wall clocks can jump backwards (NTP correction, manual change). 
For *measuring how long code took*, use `System.nanoTime()` — a monotonic counter that only ever increases. It's not epoch-based, so the absolute value is meaningless; only differences are:




