reference :

Singleton


    public class Singleton {


        // volatile ensures that when one thread updates 'instance', all other threads
        // immediately see the updated value (prevents caching issues in multi-threading)
        // static means there's only ONE instance shared across the entire class, not per object
        // private so that access is via getInstance() function only (no direct access)


        private static volatile Singleton instance;


        // private constructor prevents other classes from creating new instances
        // This forces everyone to use getInstance() instead

        private Singleton() {}

        // static method so you can call it without creating an object first
        // (Singleton.getInstance() works because it's static)
        // public so anyone can access it to get the single instance
        public static Singleton getInstance() {

            if (instance == null) {  // First check (no locking)

                synchronized (Singleton.class) {

                    if (instance == null) {  // Second check (with locking)

                        instance = new Singleton();
                    }
                }
            }
            return instance;
        }
    }



Approach 2: Inner Static Builder (Most Common) ⭐


public class Singleton {

    // Member variables - each Singleton instance has these
    private String configValue;
    private int connectionCount;


    // private constructor prevents other classes from creating new instances
    // Initialize member variables here
    private Singleton() {
        this.configValue = "default-config";
        this.connectionCount = 0;
    }

    // Inner static class - loaded only when getInstance() is called (lazy initialization)
    // This ensures thread safety without synchronization overhead
    private static class SingletonHelper {
        // final means once created, INSTANCE can never be reassigned
        // static means one shared instance for all
        private static final Singleton INSTANCE = new Singleton();
    }

    // static so you can call it without creating an object first
    // public so anyone can access it to get the single instance
    public static Singleton getInstance() {
        return SingletonHelper.INSTANCE;
    }

    // Public methods to access/modify member variables
    public String getConfigValue() {
        return configValue;
    }
}







Builder : 


public class Pizza {
    // final means once set in constructor, these values can NEVER change
    // Can only be read via getters, ensuring immutability
    private final String size;          // Required
    private final boolean olives;       // Optional
    
    // private constructor prevents direct creation: can't do "new Pizza()"
    // Forces use of the Builder pattern for object creation
    private Pizza(Builder builder) {
        this.size = builder.size;
        this.olives = builder.olives;
    }

    // public so anyone can call it: Pizza.builder()
    // static so you can call it on the class itself without needing a Pizza object first
    // Returns a new Builder to start the building process
    public static Builder builder() {
        return new Builder();
    }

    // static so it can be accessed without a Pizza instance (Pizza.Builder)
    // public so it can be used from outside this class
    // Note: Inner classes are NOT always static - we make this one static
    // because it doesn't need access to an outer Pizza instance
    public static class Builder {
        // These are NOT final - they need to be modified as we build
        private String size;
        private boolean olives = false;
        
        // Returns 'this' (the Builder itself) to allow chaining: .size().cheese().build()
        public Builder size(String size) {
            this.size = size;
            return this;  // Return Builder for method chaining
        }

        // Final step: creates and returns the actual Pizza object
        // Passes 'this' Builder to Pizza's private constructor
        public Pizza build() {
            return new Pizza(this);
        }
    }
    
    // Getters only - no setters because fields are final (immutable)
    public String getSize() {
        return size;
    }
}

// Usage: method chaining works because each method returns the Builder
Pizza pizza = Pizza.builder()    // Gets a new Builder
    .size("Large")                // Returns the Builder with size set
    .olives(true)                 // Returns the Builder with olives set
    .build();                     // Returns the final Pizza object











// STEP 1: Define Strategy Interface
interface PaymentStrategy {
    void pay(double amount);}
// STEP 2: Create Concrete Strategy Classes
class CreditCardStrategy implements PaymentStrategy {
    private String name;
    public CreditCardStrategy(String cardNumber, String name) {
        this.name = name;    }
    @Override
    public void pay(double amount) {
        System.out.println(amount + " paid using Credit Card");    }
}
class PayPalStrategy implements PaymentStrategy {
    private String email;
    public PayPalStrategy(String email) {this.email = email;}
    @Override
    public void pay(double amount) {
        System.out.println(amount + " paid using PayPal");}
}
// STEP 3: Context Class (Constructor Injection)
class ShoppingCart {
    private PaymentStrategy paymentStrategy;
    // Constructor Injection
    public ShoppingCart(PaymentStrategy paymentStrategy) {
        this.paymentStrategy = paymentStrategy;}
    public void checkout(double amount) {
        paymentStrategy.pay(amount);}
}
public class StrategyPatternDemo {
    public static void main(String[] args) {
        PaymentStrategy creditCard = new CreditCardStrategy("1234-5678", "John Doe");
        ShoppingCart cart1 = new ShoppingCart(creditCard);
        cart1.checkout(100.0);
        ShoppingCart cart2 = new ShoppingCart(paypal);
        cart2.checkout(200.0);}
}





// Step 1: Common interface
interface Pizza {
    void prepare();}
// Step 2: Concrete implementations
class MargheritaPizza implements Pizza {
    public void prepare() { System.out.println("Preparing Margherita"); }}
// Step 3: THE FACTORY 🏭
class PizzaFactory {
    public static Pizza createPizza(String type) {
        Pizza pizza = null;
        if (type.equals("margherita")) {
            pizza = new MargheritaPizza();
        } else if (type.equals("pepperoni")) {
        }
        return pizza;}
}
Pizza pizza = PizzaFactory.createPizza("pepperoni");
pizza.prepare();}





Step 1 :

1. **public** - Yes, if you want to use it from other classes. Can be package-private (no modifier) if only used within the same package.

2. **Days or DAYS** - `Days` (capitalized like a class name). The enum constants inside are UPPERCASE: `MONDAY`, `TUESDAY`, etc.

```java
public enum Days {
    MONDAY, TUESDAY, WEDNESDAY  // Constants are UPPERCASE
}
```

public enum Days {

}



Step 2 :


**Semicolon not needed** if you only have enum constants.

**Semicolon IS needed** if you add methods, constructors, or fields after the constants.

```java
// No semicolon needed
public enum Days {
    MONDAY, TUESDAY, WEDNESDAY
}

// Semicolon needed when adding methods/fields
public enum Days {
    MONDAY, TUESDAY, WEDNESDAY;  // Semicolon required here
    
    public void printDay() {
        System.out.println(this);
    }
}
```


Step 3 :

public enum Days {
    MONDAY(1), TUESDAY(2), WEDNESDAY(3);  // Semicolon required here
    
    public int val;

    private Days(int val){
        this.val=val;
    }

}


**Issues:**

1. **`val` should be `private final`** - enum fields should be immutable (can't change after creation)
2. **Constructor is already `private` by default** - but explicitly writing it is good for clarity
3. **Need a getter method** - since `val` should be private

**Corrected version:**

```java
public enum Days {
    MONDAY(1), TUESDAY(2), WEDNESDAY(3);  // Semicolon required
    
    private final int val;  // private = controlled access, final = can't change

    private Days(int val) {  // private constructor (default for enums anyway)
        this.val = val;
    }
    
    public int getVal() {  // Getter to access the private field
        return val;
    }
}

// Usage:
Days.MONDAY.getVal();  // Returns 1
```

**Summary of changes:**
- `public int val` → `private final int val`
- Added `getVal()` getter method




now what if i waana use this enum as a member variable in some other class?


public class Custom {
    Days day;
    public Custom(Days day){
        this.day=day;
    }


}





**That's correct!** Here's the complete picture with best practices:

```java
public class Custom {
    private Days day;  // private for encapsulation (better than package-private)
    
    public Custom(Days day) {
        this.day = day;
    }
    
    // Getter to access the private field
    public Days getDay() {
        return day;
    }
    
    // Optional: Setter if you want to change it later
    public void setDay(Days day) {
        this.day = day;
    }
}

// Usage:
Custom custom = new Custom(Days.MONDAY);
System.out.println(custom.getDay());  // MONDAY
System.out.println(custom.getDay().getVal());  // 1
```

**What you should add:**
- Make `day` **private** (better encapsulation)
- Add **getter** (and setter if needed)

Your approach is correct - just missing the `private` keyword and getter method!





now if i waana do some logic on that enum field, how to do?



Days day = <already defined assume>;'

switch (day) {
    case MONDAY :
        {normal code block with a break;??}
    default :
        {normal code block ?}
}









```java
Days day = Days.MONDAY;  // Already defined

switch (day) {
    case MONDAY:
        System.out.println("Start of the week!");
        // Your logic here
        break;  // break is needed to stop fall-through
        
    case TUESDAY:
    case WEDNESDAY:
        System.out.println("Midweek days");
        break;
        
    default:
        System.out.println("Other day");
        break;  // Optional in default, but good practice
}
```

**Key points:**
- **No curly braces needed** for case blocks (but you can add them if you want)
- **`break;` is required** to prevent fall-through to next case
- **`default:`** handles any case not explicitly listed
- **Multiple cases can share logic** (like TUESDAY and WEDNESDAY above)

**With curly braces (optional):**
```java
switch (day) {
    case MONDAY: {
        System.out.println("Start of the week!");
        break;
    }
    default: {
        System.out.println("Other day");
        break;
    }
}
```

Both styles work - choose based on your preference!









Add functions that use member variables

public enum Days {
    MONDAY(1), TUESDAY(2), WEDNESDAY(3);  // Semicolon required
    
    private final int val;  // private = controlled access, final = can't change

    private Days(int val) {  // private constructor (default for enums anyway)
        this.val = val;
    }
    
    public int getVal() {  // Getter to access the private field
        return val;
    }

    public int customFunc(////no need to pass something here???){
        return 10*val;      /// i have access to member variables directly iside a member function??
    }
}




**Yes, exactly right!**

Each enum constant (`MONDAY`, `TUESDAY`, etc.) is:
- A **final object** (can't be changed or reassigned)
- Created **once** when the enum is loaded
- Accessed like a **static constant** (`Days.MONDAY`)
- Used like a **normal object** (can call methods on it)

```java
// Think of it like this behind the scenes:
public final class Days {
    // Each constant is a static final instance of Days
    public static final Days MONDAY = new Days(1);
    public static final Days TUESDAY = new Days(2);
    public static final Days WEDNESDAY = new Days(3);
    
    private final int val;
    
    private Days(int val) {
        this.val = val;
    }
    
    public int customFunc() {
        return 10 * val;
    }
}

// Usage - just like calling methods on any object:
Days day = Days.MONDAY;        // Get the static final object
int result = day.customFunc(); // Call method on that object (returns 10)

// Or directly:
Days.MONDAY.customFunc();      // Call method on the static object directly
```

**Summary:** Enum constants = static final objects, accessed like static constants, used like normal objects!












public enum Days {
    MONDAY(1), TUESDAY(2), WEDNESDAY(3);  // Semicolon required
    
    private final int val;  // private = controlled access, final = can't change

    private Days(int val) {  // private constructor (default for enums anyway)
        this.val = val;
    }
    
    public int getVal() {  // Getter to access the private field
        return val;
    }

    public int customFunc(////no need to pass something here???){
        return 10*val;      /// i have access to member variables directly iside a member function??
    }

    public abstract int customFunctionPerEnum(?? here i get params from outside the enum right??){
        //what all things i have access to here? this?
    }
}


Days day = Days.MONDAY;        // Get the static final object
int result = day.customFunc(); // Call method on that object (returns 10)

// Or directly:
Days.MONDAY.customFunc();      // Call method on the static object directly






**Abstract methods in enums work differently** - each enum constant must provide its own implementation!

```java
public enum Days {
    // Each constant provides its own implementation of abstract method
    MONDAY(1) {
        @Override
        public String customFunctionPerEnum(String prefix) {
            return prefix + " - Start of week! Value: " + this.getVal();
        }
    },
    TUESDAY(2) {
        @Override
        public String customFunctionPerEnum(String prefix) {
            return prefix + " - Second day. Value: " + this.getVal();
        }
    },
    WEDNESDAY(3) {
        @Override
        public String customFunctionPerEnum(String prefix) {
            return prefix + " - Midweek. Value: " + this.getVal();
        }
    };
    
    private final int val;

    private Days(int val) {
        this.val = val;
    }
    
    public int getVal() {
        return val;
    }

    // Abstract method - each constant MUST implement this
    // Yes, you can have parameters from outside
    // you will have access to this inside this func
    public abstract String customFunctionPerEnum(String prefix);
}

// Usage:
Days.MONDAY.customFunctionPerEnum("Hello");    // "Hello - Start of week! Value: 1"
Days.TUESDAY.customFunctionPerEnum("Hello");   // "Hello - Second day. Value: 2"
```

**Inside each implementation you have access to:**
- **Parameters** passed in (`prefix` in this example)
- **`this`** - the current enum constant
- **Member variables** via `this.getVal()` or direct access to `val` if in same scope
- **Other methods** defined in the enum

Each enum constant provides its own unique behavior!














// Example of using LinkedHashMap for LRU cache
Map<K,V> cache = new LinkedHashMap<K,V>(maxSize, 0.75f, true) {
    @Override
    protected boolean removeEldestEntry(Map.Entry<K,V> eldest) {
        return size() > maxSize;  // evict oldest when capacity exceeded
    }
};



public enum HttpStatus {
    OK(200, "Success"){
        @Override
        public double apply(HttpStatus a, HttpStatus b) { return a.code + b.code; }
    },
    NOT_FOUND(404, "Not Found"),
    private final int code;
    private final String message;
    // Constructor MUST be private or package-private
    HttpStatus(int code, String message) {
        this.code = code;
        this.message = message;
    }
    public int getCode() { return code; }
    public String getMessage() { return message; }
    public abstract double apply(double a, double b);
    public boolean isLargerThan(HttpStatus other) {
        return this.code > other.code;
    }
}



public class LedgerException extends Exception {
    private final ErrorCode errorCode;
    private final String details;
    public LedgerException(ErrorCode errorCode) {
        super(errorCode.getMessage());
        this.errorCode = errorCode;
        this.details = null;
    }
    public LedgerException(ErrorCode errorCode, String details, Throwable cause) {
        super(errorCode.getMessage() + ": " + details, cause);
        this.errorCode = errorCode;
        this.details = details;
    }
    public ErrorCode getErrorCode() {return errorCode;}
    public String getDetails() {return details;}
    public int getHttpStatus() {return errorCode.getHttpStatus();}
}