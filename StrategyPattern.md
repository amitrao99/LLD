
**The Strategy pattern is a behavioral design pattern that lets you define a family of algorithms, encapsulate each one as a separate class, and make them interchangeable.**

Think of it this way: Instead of having one class with multiple conditional statements (if/else or switch) to choose different behaviors, you extract each behavior into its own class. The main class then delegates the work to one of these behavior classes.

### Core Components:

1. **Strategy Interface** - Defines the common interface for all algorithms
2. **Concrete Strategies** - Different implementations of the strategy interface (the actual algorithms)
3. **Context** - The class that uses a Strategy. It maintains a reference to a Strategy object and delegates the algorithm execution to it

### Simple Example:

Imagine a payment system:

```java
// Strategy Interface
interface PaymentStrategy {
    void pay(int amount);
}

// Concrete Strategies
class CreditCardPayment implements PaymentStrategy {
    public void pay(int amount) {
        System.out.println("Paid " + amount + " using Credit Card");
    }
}

class PayPalPayment implements PaymentStrategy {
    public void pay(int amount) {
        System.out.println("Paid " + amount + " using PayPal");
    }
}

// Context
class ShoppingCart {
    private PaymentStrategy paymentStrategy;
    
    public void setPaymentStrategy(PaymentStrategy strategy) {
        this.paymentStrategy = strategy;
    }
    
    public void checkout(int amount) {
        paymentStrategy.pay(amount);
    }
}
```

**The key idea:** The behavior (payment method) can be changed at runtime by swapping the strategy object.

---

## 2. Why Use Strategy Pattern? - Problems It Solves

### The Problems Without Strategy Pattern:

**Problem 1: Messy Conditional Logic**
```java
class PaymentProcessor {
    public void processPayment(String type, int amount) {
        if (type.equals("CREDIT_CARD")) {
            // Credit card logic
            System.out.println("Processing credit card...");
        } else if (type.equals("PAYPAL")) {
            // PayPal logic
            System.out.println("Processing PayPal...");
        } else if (type.equals("BITCOIN")) {
            // Bitcoin logic
            System.out.println("Processing Bitcoin...");
        }
        // What if we need to add 10 more payment methods?
    }
}
```

**Issues:**
- Violates Open/Closed Principle (you must modify existing code to add new behavior)
- Hard to test individual payment methods
- The class becomes bloated and hard to maintain
- All payment logic is tightly coupled in one place

---

### How Strategy Pattern Solves These:

**Solution: Extract each behavior into its own class**

```java
// Now adding a new payment method is just creating a new class
class CryptoPayment implements PaymentStrategy {
    public void pay(int amount) {
        System.out.println("Paid with Crypto");
    }
}
```

---

### Real-World Use Cases:

1. **Sorting Algorithms** - Different sorting strategies (QuickSort, MergeSort, BubbleSort) based on data size
2. **Compression** - Different compression algorithms (ZIP, RAR, GZIP)
3. **Navigation Routes** - Walking, driving, cycling routes in a map app
4. **Validation Rules** - Different validation strategies for different form fields
5. **Pricing Strategies** - Regular price, discount, seasonal pricing
6. **Authentication** - OAuth, JWT, Basic Auth

---

### Key Benefits:

✅ **Open/Closed Principle** - Open for extension, closed for modification  
✅ **Single Responsibility** - Each strategy class has one job  
✅ **Runtime Flexibility** - Switch behaviors on the fly  
✅ **Easier Testing** - Test each strategy independently  
✅ **Eliminates Conditionals** - No more long if/else chains  

---

Ready to move to **the different ways to implement Strategy pattern**?








## 3. Different Ways to Implement Strategy Pattern

Let me show you the various approaches with examples:

---

### **Approach 1: Traditional - Setter Injection**

```java
// Strategy Interface
interface PaymentStrategy {
    void pay(int amount);
}

// Concrete Strategies
class CreditCardPayment implements PaymentStrategy {
    public void pay(int amount) {
        System.out.println("Credit Card: $" + amount);
    }
}

class PayPalPayment implements PaymentStrategy {
    public void pay(int amount) {
        System.out.println("PayPal: $" + amount);
    }
}

// Context with Setter
class ShoppingCart {
    private PaymentStrategy strategy;
    
    public void setPaymentStrategy(PaymentStrategy strategy) {
        this.strategy = strategy;
    }
    
    public void checkout(int amount) {
        strategy.pay(amount);
    }
}

// Usage
ShoppingCart cart = new ShoppingCart();
cart.setPaymentStrategy(new CreditCardPayment());
cart.checkout(100);

cart.setPaymentStrategy(new PayPalPayment());
cart.checkout(200);
```

**When to use:** When you need to change strategy multiple times during object lifetime.

---

### **Approach 2: Constructor Injection**

```java
class ShoppingCart {
    private PaymentStrategy strategy;
    
    // Strategy passed at creation time
    public ShoppingCart(PaymentStrategy strategy) {
        this.strategy = strategy;
    }
    
    public void checkout(int amount) {
        strategy.pay(amount);
    }
}

// Usage
ShoppingCart cart1 = new ShoppingCart(new CreditCardPayment());
cart1.checkout(100);

ShoppingCart cart2 = new ShoppingCart(new PayPalPayment());
cart2.checkout(200);
```

**When to use:** When strategy is set once and doesn't change (immutability preferred).

---

### **Approach 3: Functional Interface + Lambda (Java 8+)** ⭐ Modern!

```java
// Functional interface
@FunctionalInterface
interface PaymentStrategy {
    void pay(int amount);
}

class ShoppingCart {
    private PaymentStrategy strategy;
    
    public void setPaymentStrategy(PaymentStrategy strategy) {
        this.strategy = strategy;
    }
    
    public void checkout(int amount) {
        strategy.pay(amount);
    }
}

// Usage with Lambdas - No need for separate classes!
ShoppingCart cart = new ShoppingCart();

cart.setPaymentStrategy(amount -> 
    System.out.println("Credit Card: $" + amount));
cart.checkout(100);

cart.setPaymentStrategy(amount -> 
    System.out.println("PayPal: $" + amount));
cart.checkout(200);
```

**When to use:** Simple strategies with single method. Very clean and concise!

---

### **Approach 4: Using Enums (Fixed Set of Strategies)**

```java
enum PaymentStrategy {
    CREDIT_CARD {
        public void pay(int amount) {
            System.out.println("Credit Card: $" + amount);
        }
    },
    PAYPAL {
        public void pay(int amount) {
            System.out.println("PayPal: $" + amount);
        }
    },
    BITCOIN {
        public void pay(int amount) {
            System.out.println("Bitcoin: $" + amount);
        }
    };
    
    public abstract void pay(int amount);
}

class ShoppingCart {
    private PaymentStrategy strategy;
    
    public void setPaymentStrategy(PaymentStrategy strategy) {
        this.strategy = strategy;
    }
    
    public void checkout(int amount) {
        strategy.pay(amount);
    }
}

// Usage
ShoppingCart cart = new ShoppingCart();
cart.setPaymentStrategy(PaymentStrategy.CREDIT_CARD);
cart.checkout(100);

cart.setPaymentStrategy(PaymentStrategy.PAYPAL);
cart.checkout(200);
```

**When to use:** Fixed, known set of strategies that won't change.

---

### **Approach 5: Anonymous Classes (One-off Strategies)**

```java
ShoppingCart cart = new ShoppingCart();

// Define strategy on the fly
cart.setPaymentStrategy(new PaymentStrategy() {
    public void pay(int amount) {
        System.out.println("Custom Payment: $" + amount);
    }
});
cart.checkout(100);
```

**When to use:** Quick, one-time use strategies. Though lambdas are cleaner for this.

---

### **Approach 6: Method References**

```java
class PaymentProcessor {
    public void processCreditCard(int amount) {
        System.out.println("Credit Card: $" + amount);
    }
    
    public void processPayPal(int amount) {
        System.out.println("PayPal: $" + amount);
    }
}

// Usage
PaymentProcessor processor = new PaymentProcessor();
ShoppingCart cart = new ShoppingCart();

cart.setPaymentStrategy(processor::processCreditCard);
cart.checkout(100);

cart.setPaymentStrategy(processor::processPayPal);
cart.checkout(200);
```

**When to use:** When you have existing methods that match the strategy signature.

---

## Quick Comparison:

| Approach | Best For | Flexibility | Verbosity |
|----------|----------|-------------|-----------|
| Traditional Classes | Complex strategies with state | High | High |
| Lambdas | Simple, stateless strategies | Medium | Low |
| Enums | Fixed set of strategies | Low | Medium |
| Anonymous Classes | Quick one-offs | Medium | High |

---

Ready to pick **one pattern to master deeply**? I'd recommend either **Traditional with Constructor Injection** (enterprise standard) or **Functional/Lambda approach** (modern and clean). Which direction interests you more?
















**You're thinking 100% CORRECT!** 

For interviews, **Traditional Constructor Injection** is the way to go. Here's why:

### Why Traditional > Lambda for Interviews:

1. **Shows Full Understanding** - Interviewers want to see you understand OOP, interfaces, and class design. Lambdas might look like you're taking shortcuts.

2. **Easy to Extend** - During interviews, they often say "Now add another strategy" or "Add some state to your strategy". With classes, this is trivial. With lambdas, you'd have to refactor.

3. **Demonstrates SOLID** - You explicitly show:
   - **S**ingle Responsibility (each strategy class does one thing)
   - **O**pen/Closed (add new strategies without changing existing code)
   - **L**iskov Substitution (strategies are interchangeable)
   - **I**nterface Segregation (clean interface)
   - **D**ependency Inversion (depend on abstraction)

4. **Clear Communication** - Interviewers can easily follow your code. Verbose is GOOD in interviews because it shows your thought process.

5. **Industry Standard** - Most companies still use traditional OOP patterns in their codebases.

---

## The ONE Pattern to Master (Interview-Ready)

Let me give you a **template you can memorize and reproduce in any interview**:

```java
// STEP 1: Define Strategy Interface
interface PaymentStrategy {
    void pay(double amount);
}

// STEP 2: Create Concrete Strategy Classes
class CreditCardStrategy implements PaymentStrategy {
    private String cardNumber;
    private String name;
    
    public CreditCardStrategy(String cardNumber, String name) {
        this.cardNumber = cardNumber;
        this.name = name;
    }
    
    @Override
    public void pay(double amount) {
        System.out.println(amount + " paid using Credit Card");
    }
}

class PayPalStrategy implements PaymentStrategy {
    private String email;
    
    public PayPalStrategy(String email) {
        this.email = email;
    }
    
    @Override
    public void pay(double amount) {
        System.out.println(amount + " paid using PayPal");
    }
}

class CashStrategy implements PaymentStrategy {
    @Override
    public void pay(double amount) {
        System.out.println(amount + " paid in Cash");
    }
}

// STEP 3: Context Class (Constructor Injection)
class ShoppingCart {
    private PaymentStrategy paymentStrategy;
    
    // Constructor Injection
    public ShoppingCart(PaymentStrategy paymentStrategy) {
        this.paymentStrategy = paymentStrategy;
    }
    
    public void checkout(double amount) {
        // Could add validation, calculations, etc.
        paymentStrategy.pay(amount);
    }
}

// STEP 4: Client/Main Usage
public class StrategyPatternDemo {
    public static void main(String[] args) {
        // Create strategies
        PaymentStrategy creditCard = new CreditCardStrategy("1234-5678", "John Doe");
        PaymentStrategy paypal = new PayPalStrategy("john@email.com");
        PaymentStrategy cash = new CashStrategy();
        
        // Use different strategies
        ShoppingCart cart1 = new ShoppingCart(creditCard);
        cart1.checkout(100.0);
        
        ShoppingCart cart2 = new ShoppingCart(paypal);
        cart2.checkout(200.0);
        
        ShoppingCart cart3 = new ShoppingCart(cash);
        cart3.checkout(50.0);
    }
}
```

---

## The Mental Model to Remember (4 Steps):

1. **Interface** - Define what all strategies must do
2. **Concrete Classes** - Implement the interface (2-3 examples)
3. **Context** - Takes strategy via constructor, uses it
4. **Client** - Creates strategies and passes to context

---

## Interview Pro Tips:

✅ **Start by explaining the problem** - "Without Strategy pattern, we'd have if/else statements that violate Open/Closed principle"

✅ **Draw a UML diagram** (if whiteboard) - Shows you think architecturally

✅ **Add meaningful state to strategies** - Like `cardNumber`, `email` - shows you understand they're real objects, not just functions

✅ **Mention benefits** - "This makes it easy to add new payment methods without changing existing code"

✅ **Be ready to extend** - If they say "add Bitcoin payment", you just create a new class

❌ **Don't over-engineer** - No need for factories, builders, etc. unless they specifically ask

❌ **Don't use lambdas** - Unless they specifically ask for Java 8+ features

---

**My advice: Practice writing this exact structure 3-4 times from memory. Change the domain (sorting, compression, discount calculation) but keep the structure identical. That's your interview superpower!**

Want to do a practice round where I give you a problem and you implement it using this pattern?






Excellent! Let's dive into **real-world complexity**. I'll show you different scenarios that go way beyond simple examples.

---

## Scenario 1: Complex Strategy with Internal State & Logic

**Problem:** E-commerce discount calculation with business rules

```java
// Strategy Interface
interface DiscountStrategy {
    double calculateDiscount(Order order);
    boolean isApplicable(Order order);
}

// Supporting Classes
class Order {
    private double totalAmount;
    private String customerType; // "NEW", "REGULAR", "VIP"
    private int itemCount;
    private boolean hasPromoCode;
    
    // Constructor, getters...
    public Order(double totalAmount, String customerType, int itemCount, boolean hasPromoCode) {
        this.totalAmount = totalAmount;
        this.customerType = customerType;
        this.itemCount = itemCount;
        this.hasPromoCode = hasPromoCode;
    }
    
    public double getTotalAmount() { return totalAmount; }
    public String getCustomerType() { return customerType; }
    public int getItemCount() { return itemCount; }
    public boolean hasPromoCode() { return hasPromoCode; }
}

// Complex Strategy 1: Tiered Discount with Multiple Rules
class TieredDiscountStrategy implements DiscountStrategy {
    private static final double TIER1_THRESHOLD = 100.0;
    private static final double TIER2_THRESHOLD = 500.0;
    private static final double TIER3_THRESHOLD = 1000.0;
    
    private double tier1Percent;
    private double tier2Percent;
    private double tier3Percent;
    
    public TieredDiscountStrategy(double tier1, double tier2, double tier3) {
        this.tier1Percent = tier1;
        this.tier2Percent = tier2;
        this.tier3Percent = tier3;
    }
    
    @Override
    public boolean isApplicable(Order order) {
        return order.getTotalAmount() >= TIER1_THRESHOLD;
    }
    
    @Override
    public double calculateDiscount(Order order) {
        double amount = order.getTotalAmount();
        double discount = 0;
        
        if (amount >= TIER3_THRESHOLD) {
            discount = amount * tier3Percent;
        } else if (amount >= TIER2_THRESHOLD) {
            discount = amount * tier2Percent;
        } else if (amount >= TIER1_THRESHOLD) {
            discount = amount * tier1Percent;
        }
        
        // Additional logic: cap discount at 30% of order
        double maxDiscount = amount * 0.30;
        return Math.min(discount, maxDiscount);
    }
}

// Complex Strategy 2: Loyalty Points with Accumulation Logic
class LoyaltyPointsDiscountStrategy implements DiscountStrategy {
    private LoyaltyPointsService loyaltyService; // External dependency
    private String customerId;
    private int pointsToRedeem;
    
    public LoyaltyPointsDiscountStrategy(LoyaltyPointsService service, 
                                         String customerId, 
                                         int pointsToRedeem) {
        this.loyaltyService = service;
        this.customerId = customerId;
        this.pointsToRedeem = pointsToRedeem;
    }
    
    @Override
    public boolean isApplicable(Order order) {
        int availablePoints = loyaltyService.getPoints(customerId);
        return availablePoints >= pointsToRedeem && order.getTotalAmount() > 50;
    }
    
    @Override
    public double calculateDiscount(Order order) {
        if (!isApplicable(order)) {
            return 0;
        }
        
        // Complex calculation: 100 points = $1 discount
        double discount = pointsToRedeem / 100.0;
        
        // Deduct points (side effect!)
        loyaltyService.deductPoints(customerId, pointsToRedeem);
        
        // Award new points for this purchase
        int earnedPoints = (int) (order.getTotalAmount() * 0.1);
        loyaltyService.addPoints(customerId, earnedPoints);
        
        return discount;
    }
}

// Complex Strategy 3: Seasonal/Time-based with Blackout Dates
class SeasonalDiscountStrategy implements DiscountStrategy {
    private LocalDate startDate;
    private LocalDate endDate;
    private Set<LocalDate> blackoutDates;
    private double discountPercent;
    
    public SeasonalDiscountStrategy(LocalDate start, LocalDate end, 
                                    double discountPercent, 
                                    Set<LocalDate> blackoutDates) {
        this.startDate = start;
        this.endDate = end;
        this.discountPercent = discountPercent;
        this.blackoutDates = blackoutDates;
    }
    
    @Override
    public boolean isApplicable(Order order) {
        LocalDate today = LocalDate.now();
        boolean inSeason = !today.isBefore(startDate) && !today.isAfter(endDate);
        boolean notBlackedOut = !blackoutDates.contains(today);
        
        return inSeason && notBlackedOut;
    }
    
    @Override
    public double calculateDiscount(Order order) {
        if (!isApplicable(order)) {
            return 0;
        }
        return order.getTotalAmount() * discountPercent;
    }
}

// Mock service for demonstration
class LoyaltyPointsService {
    private Map<String, Integer> pointsDatabase = new HashMap<>();
    
    public int getPoints(String customerId) {
        return pointsDatabase.getOrDefault(customerId, 0);
    }
    
    public void deductPoints(String customerId, int points) {
        int current = getPoints(customerId);
        pointsDatabase.put(customerId, current - points);
    }
    
    public void addPoints(String customerId, int points) {
        int current = getPoints(customerId);
        pointsDatabase.put(customerId, current + points);
    }
}

// Context with validation and error handling
class PricingEngine {
    private DiscountStrategy discountStrategy;
    
    public PricingEngine(DiscountStrategy discountStrategy) {
        if (discountStrategy == null) {
            throw new IllegalArgumentException("Discount strategy cannot be null");
        }
        this.discountStrategy = discountStrategy;
    }
    
    public double calculateFinalPrice(Order order) {
        if (order == null || order.getTotalAmount() <= 0) {
            throw new IllegalArgumentException("Invalid order");
        }
        
        double discount = 0;
        
        if (discountStrategy.isApplicable(order)) {
            discount = discountStrategy.calculateDiscount(order);
            System.out.println("Discount applied: $" + discount);
        } else {
            System.out.println("Discount not applicable for this order");
        }
        
        double finalPrice = order.getTotalAmount() - discount;
        return Math.max(finalPrice, 0); // Never negative
    }
}
```

**Key Complexity Points:**
- ✅ Strategies have **internal state** (thresholds, dates, service dependencies)
- ✅ Strategies have **complex business logic** (tiered calculations, date ranges)
- ✅ Strategies can have **side effects** (deducting loyalty points)
- ✅ Strategies validate their applicability (`isApplicable` method)
- ✅ Context has **validation and error handling**

---

## Scenario 2: Runtime Strategy Selection Based on Conditions

**Problem:** Choose compression strategy based on file type and size

```java
// Strategy Interface
interface CompressionStrategy {
    byte[] compress(byte[] data);
    String getAlgorithmName();
}

// Concrete Strategies
class GzipCompressionStrategy implements CompressionStrategy {
    private int compressionLevel; // 1-9
    
    public GzipCompressionStrategy(int level) {
        this.compressionLevel = level;
    }
    
    @Override
    public byte[] compress(byte[] data) {
        System.out.println("Compressing with GZIP (level " + compressionLevel + ")");
        // Actual GZIP compression logic
        return data; // Simplified
    }
    
    @Override
    public String getAlgorithmName() {
        return "GZIP";
    }
}

class LZ4CompressionStrategy implements CompressionStrategy {
    @Override
    public byte[] compress(byte[] data) {
        System.out.println("Compressing with LZ4 (fast)");
        // Actual LZ4 compression logic
        return data; // Simplified
    }
    
    @Override
    public String getAlgorithmName() {
        return "LZ4";
    }
}

class NoCompressionStrategy implements CompressionStrategy {
    @Override
    public byte[] compress(byte[] data) {
        System.out.println("No compression applied");
        return data;
    }
    
    @Override
    public String getAlgorithmName() {
        return "NONE";
    }
}

// Strategy Factory/Selector
class CompressionStrategySelector {
    
    public static CompressionStrategy selectStrategy(String fileType, long fileSizeBytes) {
        
        // Rule 1: Small files - no compression (overhead not worth it)
        if (fileSizeBytes < 1024) { // < 1KB
            return new NoCompressionStrategy();
        }
        
        // Rule 2: Images - use fast compression
        if (fileType.matches(".*\\.(jpg|jpeg|png|gif)$")) {
            return new LZ4CompressionStrategy();
        }
        
        // Rule 3: Text files - use high compression
        if (fileType.matches(".*\\.(txt|log|csv|json|xml)$")) {
            return new GzipCompressionStrategy(9); // Max compression
        }
        
        // Rule 4: Large files - use medium compression for balance
        if (fileSizeBytes > 10_000_000) { // > 10MB
            return new GzipCompressionStrategy(6); // Balanced
        }
        
        // Default: Fast compression
        return new LZ4CompressionStrategy();
    }
}

// Context with Strategy Selection
class FileCompressor {
    private CompressionStrategy strategy;
    private String fileName;
    private long fileSize;
    
    public FileCompressor(String fileName, long fileSize) {
        this.fileName = fileName;
        this.fileSize = fileSize;
        // Runtime strategy selection based on file properties
        this.strategy = CompressionStrategySelector.selectStrategy(fileName, fileSize);
    }
    
    // Alternative: Allow manual override
    public void setCompressionStrategy(CompressionStrategy strategy) {
        this.strategy = strategy;
    }
    
    public byte[] compressFile(byte[] fileData) {
        System.out.println("File: " + fileName + " (" + fileSize + " bytes)");
        System.out.println("Selected strategy: " + strategy.getAlgorithmName());
        
        long startTime = System.nanoTime();
        byte[] compressed = strategy.compress(fileData);
        long endTime = System.nanoTime();
        
        double compressionRatio = (double) compressed.length / fileData.length;
        System.out.println("Compression ratio: " + String.format("%.2f", compressionRatio));
        System.out.println("Time: " + (endTime - startTime) / 1_000_000 + " ms\n");
        
        return compressed;
    }
}

// Usage
public class RuntimeStrategyDemo {
    public static void main(String[] args) {
        byte[] dummyData = new byte[5000];
        
        // Automatic strategy selection
        FileCompressor compressor1 = new FileCompressor("data.txt", 5000);
        compressor1.compressFile(dummyData);
        
        FileCompressor compressor2 = new FileCompressor("photo.jpg", 500000);
        compressor2.compressFile(dummyData);
        
        FileCompressor compressor3 = new FileCompressor("tiny.log", 500);
        compressor3.compressFile(dummyData);
        
        // Manual override when needed
        FileCompressor compressor4 = new FileCompressor("special.bin", 10000);
        compressor4.setCompressionStrategy(new GzipCompressionStrategy(1)); // Force specific strategy
        compressor4.compressFile(dummyData);
    }
}
```

**Key Complexity Points:**
- ✅ **Runtime strategy selection** based on file properties
- ✅ **Strategy factory/selector pattern** to encapsulate selection logic
- ✅ **Context collects metrics** (compression ratio, time)
- ✅ **Hybrid approach**: Auto-selection + manual override option

---

## Scenario 3: Strategies with Dependencies and Chaining

**Problem:** Data export with multiple transformations

```java
// Multiple related strategies
interface DataExportStrategy {
    String export(List<Customer> customers);
    String getFormat();
}

interface DataValidationStrategy {
    boolean validate(List<Customer> customers);
    List<String> getValidationErrors();
}

interface DataTransformStrategy {
    List<Customer> transform(List<Customer> customers);
}

// Domain model
class Customer {
    private String id;
    private String name;
    private String email;
    private double totalSpent;
    
    public Customer(String id, String name, String email, double totalSpent) {
        this.id = id;
        this.name = name;
        this.email = email;
        this.totalSpent = totalSpent;
    }
    
    // Getters...
    public String getId() { return id; }
    public String getName() { return name; }
    public String getEmail() { return email; }
    public double getTotalSpent() { return totalSpent; }
    public void setTotalSpent(double totalSpent) { this.totalSpent = totalSpent; }
}

// Export Strategies
class CSVExportStrategy implements DataExportStrategy {
    private String delimiter;
    
    public CSVExportStrategy(String delimiter) {
        this.delimiter = delimiter;
    }
    
    @Override
    public String export(List<Customer> customers) {
        StringBuilder csv = new StringBuilder();
        csv.append("ID").append(delimiter)
           .append("Name").append(delimiter)
           .append("Email").append(delimiter)
           .append("TotalSpent\n");
        
        for (Customer c : customers) {
            csv.append(c.getId()).append(delimiter)
               .append(c.getName()).append(delimiter)
               .append(c.getEmail()).append(delimiter)
               .append(c.getTotalSpent()).append("\n");
        }
        return csv.toString();
    }
    
    @Override
    public String getFormat() {
        return "CSV";
    }
}

class JSONExportStrategy implements DataExportStrategy {
    private boolean prettyPrint;
    
    public JSONExportStrategy(boolean prettyPrint) {
        this.prettyPrint = prettyPrint;
    }
    
    @Override
    public String export(List<Customer> customers) {
        StringBuilder json = new StringBuilder();
        String indent = prettyPrint ? "  " : "";
        String newline = prettyPrint ? "\n" : "";
        
        json.append("[").append(newline);
        for (int i = 0; i < customers.size(); i++) {
            Customer c = customers.get(i);
            json.append(indent).append("{").append(newline)
                .append(indent).append(indent).append("\"id\": \"").append(c.getId()).append("\",").append(newline)
                .append(indent).append(indent).append("\"name\": \"").append(c.getName()).append("\",").append(newline)
                .append(indent).append(indent).append("\"email\": \"").append(c.getEmail()).append("\",").append(newline)
                .append(indent).append(indent).append("\"totalSpent\": ").append(c.getTotalSpent()).append(newline)
                .append(indent).append("}");
            if (i < customers.size() - 1) json.append(",");
            json.append(newline);
        }
        json.append("]");
        return json.toString();
    }
    
    @Override
    public String getFormat() {
        return "JSON";
    }
}

// Validation Strategies
class EmailValidationStrategy implements DataValidationStrategy {
    private List<String> errors = new ArrayList<>();
    
    @Override
    public boolean validate(List<Customer> customers) {
        errors.clear();
        boolean isValid = true;
        
        for (Customer c : customers) {
            if (c.getEmail() == null || !c.getEmail().contains("@")) {
                errors.add("Invalid email for customer: " + c.getId());
                isValid = false;
            }
        }
        return isValid;
    }
    
    @Override
    public List<String> getValidationErrors() {
        return new ArrayList<>(errors);
    }
}

// Transform Strategies
class HighValueCustomerFilterStrategy implements DataTransformStrategy {
    private double threshold;
    
    public HighValueCustomerFilterStrategy(double threshold) {
        this.threshold = threshold;
    }
    
    @Override
    public List<Customer> transform(List<Customer> customers) {
        return customers.stream()
            .filter(c -> c.getTotalSpent() >= threshold)
            .collect(Collectors.toList());
    }
}

class AnonymizationStrategy implements DataTransformStrategy {
    @Override
    public List<Customer> transform(List<Customer> customers) {
        List<Customer> anonymized = new ArrayList<>();
        for (Customer c : customers) {
            String maskedEmail = c.getEmail().replaceAll("(?<=.{2}).(?=.*@)", "*");
            anonymized.add(new Customer(c.getId(), c.getName(), maskedEmail, c.getTotalSpent()));
        }
        return anonymized;
    }
}

// Complex Context with Multiple Strategies
class DataExportPipeline {
    private DataValidationStrategy validationStrategy;
    private DataTransformStrategy transformStrategy;
    private DataExportStrategy exportStrategy;
    
    // Constructor injection for all strategies
    public DataExportPipeline(DataValidationStrategy validationStrategy,
                              DataTransformStrategy transformStrategy,
                              DataExportStrategy exportStrategy) {
        this.validationStrategy = validationStrategy;
        this.transformStrategy = transformStrategy;
        this.exportStrategy = exportStrategy;
    }
    
    public String processAndExport(List<Customer> customers) {
        System.out.println("=== Starting Export Pipeline ===");
        System.out.println("Initial customer count: " + customers.size());
        
        // Step 1: Validation
        if (!validationStrategy.validate(customers)) {
            System.err.println("Validation failed:");
            for (String error : validationStrategy.getValidationErrors()) {
                System.err.println("  - " + error);
            }
            throw new RuntimeException("Data validation failed");
        }
        System.out.println("✓ Validation passed");
        
        // Step 2: Transformation
        List<Customer> transformed = transformStrategy.transform(customers);
        System.out.println("✓ Transformation applied");
        System.out.println("  Customers after transform: " + transformed.size());
        
        // Step 3: Export
        String result = exportStrategy.export(transformed);
        System.out.println("✓ Export completed in " + exportStrategy.getFormat() + " format");
        System.out.println("=== Pipeline Complete ===\n");
        
        return result;
    }
}

// Usage
public class ComplexStrategyDemo {
    public static void main(String[] args) {
        List<Customer> customers = Arrays.asList(
            new Customer("1", "Alice", "alice@email.com", 1500.0),
            new Customer("2", "Bob", "bob@email.com", 500.0),
            new Customer("3", "Charlie", "charlie@email.com", 2500.0),
            new Customer("4", "David", "invalid-email", 800.0)
        );
        
        // Pipeline 1: High-value customers to JSON
        DataExportPipeline pipeline1 = new DataExportPipeline(
            new EmailValidationStrategy(),
            new HighValueCustomerFilterStrategy(1000.0),
            new JSONExportStrategy(true)
        );
        
        try {
            String json = pipeline1.processAndExport(customers);
            System.out.println("Exported JSON:\n" + json);
        } catch (RuntimeException e) {
            System.err.println("Export failed: " + e.getMessage());
        }
        
        // Pipeline 2: All customers, anonymized, to CSV
        List<Customer> validCustomers = customers.stream()
            .filter(c -> c.getEmail().contains("@"))
            .collect(Collectors.toList());
        
        DataExportPipeline pipeline2 = new DataExportPipeline(
            new EmailValidationStrategy(),
            new AnonymizationStrategy(),
            new CSVExportStrategy(",")
        );
        
        String csv = pipeline2.processAndExport(validCustomers);
        System.out.println("Exported CSV:\n" + csv);
    }
}
```

**Key Complexity Points:**
- ✅ **Multiple strategy types** working together (validation, transform, export)
- ✅ **Pipeline pattern** - strategies executed in sequence
- ✅ **Strategies maintain state** (validation errors)
- ✅ **Error handling** integrated into pipeline
- ✅ **Real transformation logic** (filtering, anonymization)

---

## Key Takeaways for Complex Scenarios:

1. **Strategies can have state** - configuration, dependencies, accumulated data
2. **Strategies can depend on external services** - databases, APIs, other objects
3. **Strategy selection can be dynamic** - based on runtime conditions
4. **Multiple strategies can work together** - in pipelines or composition
5. **Context can be sophisticated** - validation, metrics, error handling
6. **Strategies can have side effects** - modifying external state

Would you like me to show **even more advanced scenarios** like:
- Strategy patterns with caching/memoization
- Composite strategies (combining multiple strategies)
- Strategy pattern with async/concurrent operations
- Strategy pattern with database/persistence layer

Or do you want to practice implementing one of these complex scenarios?


