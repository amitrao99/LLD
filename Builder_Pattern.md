
Perfect! Let's tackle the Builder pattern with the same thorough approach we used for Singleton.

---

## 1. What is the Builder Pattern?

**Key characteristics:**
- Constructs complex objects step-by-step
- Provides fluent/chainable API
- Separates construction logic from business logic
- Immutable objects (typically)

---

## 2. Use Cases - Why Do We Use It?

### **Problem 1: Telescoping Constructor Anti-Pattern**

**Without Builder (THE NIGHTMARE):**
```java
public class User {
    public User(String name) { ... }
    public User(String name, int age) { ... }
    public User(String name, int age, String email) { ... }
    public User(String name, int age, String email, String phone) { ... }
    public User(String name, int age, String email, String phone, String address) { ... }
    public User(String name, int age, String email, String phone, String address, String city) { ... }
    // 😱 20+ constructors!!!
}

// Using it:
User user = new User("John", 30, "john@example.com", null, null, "NYC");
                    // What are those nulls? Which parameter is which? 😵
```

**Problems:**
- ❌ Too many constructors
- ❌ Hard to read: `new User("John", 30, null, null, "NYC")` - what is what?
- ❌ Parameter order mistakes
- ❌ Can't have optional parameters easily

### **Problem 2: JavaBeans Pattern Issues**

**JavaBeans approach:**
```java
User user = new User();
user.setName("John");
user.setAge(30);
user.setEmail("john@example.com");
// Object is MUTABLE and in INCONSISTENT state between calls
// What if you forget to call setName()? Invalid object!
```

**Problems:**
- ❌ Object in inconsistent state during construction
- ❌ Not thread-safe
- ❌ Can't create immutable objects
- ❌ Can't enforce required fields

### **Solution: Builder Pattern** ✅

```java
User user = User.builder()
    .name("John")
    .age(30)
    .email("john@example.com")
    .city("NYC")
    .build();
```

**Benefits:**
- ✅ Readable and clear
- ✅ Immutable objects
- ✅ Can enforce required fields
- ✅ Optional parameters are easy
- ✅ Fluent API (method chaining)
- ✅ Thread-safe construction

---

### **When to Use Builder Pattern:**

**Use Builder when your class has:**
1. **4+ parameters** (especially if some are optional)
2. **Many optional parameters**
3. **Need for immutability**
4. **Complex object construction logic**
5. **Multiple representations** of the same data

**Real-world examples:**
- **HTTP Request builders** - `HttpRequest.newBuilder().uri(...).header(...).POST(...).build()`
- **Query builders** - SQL, MongoDB queries
- **Configuration objects** - App settings, connection configs
- **DTOs/POJOs** - User profiles, product details, orders
- **Test data builders** - Creating mock objects for tests
- **Document builders** - PDFs, reports, emails

---

## 3. Different Ways to Implement Builder Pattern

Let me show you the main approaches:

---

## **Approach 1: Classic Builder (Separate Builder Class)**

```java
public class User {
    // Final fields - immutable
    private final String name;      // Required
    private final int age;          // Required
    private final String email;     // Optional
    private final String phone;     // Optional
    private final String address;   // Optional
    
    // Private constructor - can only be called by Builder
    private User(UserBuilder builder) {
        this.name = builder.name;
        this.age = builder.age;
        this.email = builder.email;
        this.phone = builder.phone;
        this.address = builder.address;
    }
    
    // Getters only (no setters - immutable)
    public String getName() { return name; }
    public int getAge() { return age; }
    public String getEmail() { return email; }
    public String getPhone() { return phone; }
    public String getAddress() { return address; }
    
    // Static method to get builder
    public static UserBuilder builder() {
        return new UserBuilder();
    }
    
    // Separate Builder class
    public static class UserBuilder {
        // Non-final fields in builder (mutable during construction)
        private String name;
        private int age;
        private String email;
        private String phone;
        private String address;
        
        // Private constructor
        private UserBuilder() {}
        
        // Fluent setter methods (return 'this' for chaining)
        public UserBuilder name(String name) {
            this.name = name;
            return this;
        }
        
        public UserBuilder age(int age) {
            this.age = age;
            return this;
        }
        
        public UserBuilder email(String email) {
            this.email = email;
            return this;
        }
        
        public UserBuilder phone(String phone) {
            this.phone = phone;
            return this;
        }
        
        public UserBuilder address(String address) {
            this.address = address;
            return this;
        }
        
        // Build method - validates and creates User
        public User build() {
            // Validation
            if (name == null || name.isEmpty()) {
                throw new IllegalStateException("Name is required");
            }
            if (age < 0 || age > 150) {
                throw new IllegalStateException("Invalid age");
            }
            
            return new User(this);
        }
    }
}

// Usage:
User user = User.builder()
    .name("John Doe")
    .age(30)
    .email("john@example.com")
    .phone("123-456-7890")
    .build();
```

**Pros:**
- Clear separation between object and builder
- Immutable final object
- Easy to add validation
- Clean and professional

**Cons:**
- More verbose
- Duplicate field declarations

---

## **Approach 2: Inner Static Builder (Most Common)** ⭐

```java
public class Pizza {
    // Final fields
    private final String size;          // Required
    private final String crust;         // Required
    private final String cheese;        // Required
    private final boolean pepperoni;    // Optional
    private final boolean mushrooms;    // Optional
    private final boolean olives;       // Optional
    
    // Private constructor
    private Pizza(Builder builder) {
        this.size = builder.size;
        this.crust = builder.crust;
        this.cheese = builder.cheese;
        this.pepperoni = builder.pepperoni;
        this.mushrooms = builder.mushrooms;
        this.olives = builder.olives;
    }
    
    // Getters
    public String getSize() { return size; }
    public String getCrust() { return crust; }
    public String getCheese() { return cheese; }
    public boolean hasPepperoni() { return pepperoni; }
    public boolean hasMushrooms() { return mushrooms; }
    public boolean hasOlives() { return olives; }
    
    // Static method to get builder
    public static Builder builder() {
        return new Builder();
    }
    
    // Inner static Builder class
    public static class Builder {
        // Required parameters
        private String size;
        private String crust;
        private String cheese;
        
        // Optional parameters with defaults
        private boolean pepperoni = false;
        private boolean mushrooms = false;
        private boolean olives = false;
        
        public Builder size(String size) {
            this.size = size;
            return this;
        }
        
        public Builder crust(String crust) {
            this.crust = crust;
            return this;
        }
        
        public Builder cheese(String cheese) {
            this.cheese = cheese;
            return this;
        }
        
        public Builder pepperoni() {
            this.pepperoni = true;
            return this;
        }
        
        public Builder mushrooms() {
            this.mushrooms = true;
            return this;
        }
        
        public Builder olives() {
            this.olives = true;
            return this;
        }
        
        public Pizza build() {
            // Validate required fields
            if (size == null) throw new IllegalStateException("Size is required");
            if (crust == null) throw new IllegalStateException("Crust is required");
            if (cheese == null) throw new IllegalStateException("Cheese is required");
            
            return new Pizza(this);
        }
    }
    
    @Override
    public String toString() {
        return String.format("Pizza[size=%s, crust=%s, cheese=%s, pepperoni=%s, mushrooms=%s, olives=%s]",
            size, crust, cheese, pepperoni, mushrooms, olives);
    }
}

// Usage:
Pizza pizza = Pizza.builder()
    .size("Large")
    .crust("Thin")
    .cheese("Mozzarella")
    .pepperoni()
    .mushrooms()
    .build();
```

**Pros:**
- Everything in one file
- Most popular approach
- Clean and maintainable

**Cons:**
- Still some duplication

---

## **Approach 3: Lombok @Builder** ⚡

```java
import lombok.Builder;
import lombok.Getter;
import lombok.ToString;

@Getter
@Builder
@ToString
public class Product {
    private final String name;
    private final double price;
    private final String category;
    private final String description;
    private final int stock;
    private final String imageUrl;
}

// Usage - Lombok generates all the builder code!
Product product = Product.builder()
    .name("Laptop")
    .price(999.99)
    .category("Electronics")
    .description("High-performance laptop")
    .stock(50)
    .imageUrl("http://example.com/laptop.jpg")
    .build();
```

**Pros:**
- ✅ Extremely concise - just one annotation
- ✅ No boilerplate code
- ✅ Automatic generation

**Cons:**
- ❌ Requires Lombok dependency
- ❌ Less control over validation
- ❌ Magic (generated code not visible)

---

## **Approach 4: Step Builder (Enforcing Required Parameters)** 🔒

```java
// This ensures you MUST set required fields in order
public class DatabaseConfig {
    private final String host;
    private final int port;
    private final String database;
    private final String username;
    private final String password;
    private final int maxConnections;
    
    private DatabaseConfig(Builder builder) {
        this.host = builder.host;
        this.port = builder.port;
        this.database = builder.database;
        this.username = builder.username;
        this.password = builder.password;
        this.maxConnections = builder.maxConnections;
    }
    
    // Step interfaces
    public interface HostStep {
        PortStep host(String host);
    }
    
    public interface PortStep {
        DatabaseStep port(int port);
    }
    
    public interface DatabaseStep {
        UsernameStep database(String database);
    }
    
    public interface UsernameStep {
        PasswordStep username(String username);
    }
    
    public interface PasswordStep {
        BuildStep password(String password);
    }
    
    public interface BuildStep {
        BuildStep maxConnections(int maxConnections);  // Optional
        DatabaseConfig build();
    }
    
    // Builder implements all steps
    public static class Builder implements HostStep, PortStep, DatabaseStep, 
                                           UsernameStep, PasswordStep, BuildStep {
        private String host;
        private int port;
        private String database;
        private String username;
        private String password;
        private int maxConnections = 10;  // Default
        
        private Builder() {}
        
        @Override
        public PortStep host(String host) {
            this.host = host;
            return this;
        }
        
        @Override
        public DatabaseStep port(int port) {
            this.port = port;
            return this;
        }
        
        @Override
        public UsernameStep database(String database) {
            this.database = database;
            return this;
        }
        
        @Override
        public PasswordStep username(String username) {
            this.username = username;
            return this;
        }
        
        @Override
        public BuildStep password(String password) {
            this.password = password;
            return this;
        }
        
        @Override
        public BuildStep maxConnections(int maxConnections) {
            this.maxConnections = maxConnections;
            return this;
        }
        
        @Override
        public DatabaseConfig build() {
            return new DatabaseConfig(this);
        }
    }
    
    public static HostStep builder() {
        return new Builder();
    }
}

// Usage - IDE auto-completion guides you through required steps!
DatabaseConfig config = DatabaseConfig.builder()
    .host("localhost")        // Must be first
    .port(3306)              // Must be second
    .database("mydb")        // Must be third
    .username("root")        // Must be fourth
    .password("password")    // Must be fifth
    .maxConnections(20)      // Optional
    .build();
```

**Pros:**
- ✅ Compile-time enforcement of required fields
- ✅ IDE guides you through steps
- ✅ Impossible to forget required fields

**Cons:**
- ❌ Very verbose
- ❌ Complex to implement
- ❌ Overkill for most cases

---

## **Approach 5: Method Chaining without Builder Class** 

```java
// Sometimes called "Fluent API" but NOT true Builder pattern
public class EmailMessage {
    private String to;
    private String subject;
    private String body;
    
    public EmailMessage to(String to) {
        this.to = to;
        return this;
    }
    
    public EmailMessage subject(String subject) {
        this.subject = subject;
        return this;
    }
    
    public EmailMessage body(String body) {
        this.body = body;
        return this;
    }
    
    public void send() {
        System.out.println("Sending email to: " + to);
    }
}

// Usage:
new EmailMessage()
    .to("john@example.com")
    .subject("Hello")
    .body("How are you?")
    .send();
```

**Pros:**
- Simple
- Less code

**Cons:**
- ❌ Object is MUTABLE (not immutable)
- ❌ No separation of construction and representation
- ❌ Not a true Builder pattern

---

## **Quick Comparison Table**

| Approach 				| Immutability | Validation | Complexity | Use When 						|
|-----------------------|--------------|------------|------------|----------------------------------|
| Classic Builder 		| ✅ 		   | ✅ 		| Medium     | Professional projects 			|
| Inner Static Builder 	| ✅ 		   | ✅ 		| Medium     | **Most common - recommended** ⭐ |
| Lombok 				| ✅ 		   | ⚠️ Limited | Low        | Rapid development 				|
| Step Builder 			| ✅ 		   | ✅✅       | High       | Critical configs, APIs 			|
| Fluent API 			| ❌ 		   | ✅         | Low        | Simple cases only 				|

---














# 🎯 **My Recommendation: Inner Static Builder Pattern**

This is the pattern you should **master and use 90% of the time** - it's the industry standard.

---

## **Why Inner Static Builder?**

1. ✅ **Most widely used** in professional code (Spring, Hibernate, etc.)
2. ✅ **Immutable objects** by default
3. ✅ **Easy validation** in build() method
4. ✅ **Clean and readable** - everything in one file
5. ✅ **No external dependencies** (unlike Lombok)
6. ✅ **Handles complex objects** perfectly (which we'll cover!)

---

## **Handling Complex Objects in Builder**

You're absolutely right - real builders don't just use primitives! Let me show you the different strategies:

### **Strategy 1: Pass Complex Objects Directly**

```java
public class Address {
    private final String street;
    private final String city;
    private final String state;
    private final String zipCode;
    
    public Address(String street, String city, String state, String zipCode) {
        this.street = street;
        this.city = city;
        this.state = state;
        this.zipCode = zipCode;
    }
    
    // Getters...
}

public class Employee {
    private final String name;
    private final String email;
    private final Address address;  // ← Complex object!
    private final List<String> skills;  // ← Collection!
    
    private Employee(Builder builder) {
        this.name = builder.name;
        this.email = builder.email;
        this.address = builder.address;
        this.skills = builder.skills;
    }
    
    public static class Builder {
        private String name;
        private String email;
        private Address address;
        private List<String> skills = new ArrayList<>();
        
        public Builder name(String name) {
            this.name = name;
            return this;
        }
        
        public Builder email(String email) {
            this.email = email;
            return this;
        }
        
        // Accept the complex object directly
        public Builder address(Address address) {
            this.address = address;
            return this;
        }
        
        // Add individual skills
        public Builder skill(String skill) {
            this.skills.add(skill);
            return this;
        }
        
        // Or add multiple skills at once
        public Builder skills(List<String> skills) {
            this.skills.addAll(skills);
            return this;
        }
        
        public Employee build() {
            if (name == null) throw new IllegalStateException("Name required");
            if (email == null) throw new IllegalStateException("Email required");
            return new Employee(this);
        }
    }
    
    public static Builder builder() {
        return new Builder();
    }
}

// Usage:
Address address = new Address("123 Main St", "New York", "NY", "10001");

Employee emp = Employee.builder()
    .name("John Doe")
    .email("john@example.com")
    .address(address)  // Pass complex object
    .skill("Java")
    .skill("Python")
    .build();
```

---

### **Strategy 2: Builder Composition (Nested Builders)** ⭐

This is the **elegant approach** - use a builder within a builder!

```java
public class Address {
    private final String street;
    private final String city;
    private final String state;
    private final String zipCode;
    
    private Address(Builder builder) {
        this.street = builder.street;
        this.city = builder.city;
        this.state = builder.state;
        this.zipCode = builder.zipCode;
    }
    
    public static class Builder {
        private String street;
        private String city;
        private String state;
        private String zipCode;
        
        public Builder street(String street) {
            this.street = street;
            return this;
        }
        
        public Builder city(String city) {
            this.city = city;
            return this;
        }
        
        public Builder state(String state) {
            this.state = state;
            return this;
        }
        
        public Builder zipCode(String zipCode) {
            this.zipCode = zipCode;
            return this;
        }
        
        public Address build() {
            return new Address(this);
        }
    }
    
    public static Builder builder() {
        return new Builder();
    }
    
    // Getters...
    public String getStreet() { return street; }
    public String getCity() { return city; }
    public String getState() { return state; }
    public String getZipCode() { return zipCode; }
}

public class Employee {
    private final String name;
    private final String email;
    private final Address address;
    
    private Employee(Builder builder) {
        this.name = builder.name;
        this.email = builder.email;
        this.address = builder.address;
    }
    
    public static class Builder {
        private String name;
        private String email;
        private Address address;
        
        public Builder name(String name) {
            this.name = name;
            return this;
        }
        
        public Builder email(String email) {
            this.email = email;
            return this;
        }
        
        // Option 1: Accept pre-built Address
        public Builder address(Address address) {
            this.address = address;
            return this;
        }
        
        // Option 2: Accept Address.Builder (more flexible!)
        public Builder address(Address.Builder addressBuilder) {
            this.address = addressBuilder.build();
            return this;
        }
        
        public Employee build() {
            return new Employee(this);
        }
    }
    
    public static Builder builder() {
        return new Builder();
    }
}

// Usage - Beautiful nested building!
Employee emp = Employee.builder()
    .name("John Doe")
    .email("john@example.com")
    .address(Address.builder()  // ← Nested builder!
        .street("123 Main St")
        .city("New York")
        .state("NY")
        .zipCode("10001"))  // Returns Address.Builder, gets auto-built
    .build();
```

---

### **Strategy 3: Consumer Pattern (Java 8+)** 🔥

This is the **most elegant modern approach**:

```java
public class Employee {
    private final String name;
    private final String email;
    private final Address address;
    
    private Employee(Builder builder) {
        this.name = builder.name;
        this.email = builder.email;
        this.address = builder.address;
    }
    
    public static class Builder {
        private String name;
        private String email;
        private Address address;
        
        public Builder name(String name) {
            this.name = name;
            return this;
        }
        
        public Builder email(String email) {
            this.email = email;
            return this;
        }
        
        // Accept a Consumer that configures the Address.Builder!
        public Builder address(Consumer<Address.Builder> addressConfig) {
            Address.Builder addressBuilder = Address.builder();
            addressConfig.accept(addressBuilder);  // Configure it
            this.address = addressBuilder.build();
            return this;
        }
        
        public Employee build() {
            return new Employee(this);
        }
    }
    
    public static Builder builder() {
        return new Builder();
    }
}

// Usage - Lambda magic! ✨
Employee emp = Employee.builder()
    .name("John Doe")
    .email("john@example.com")
    .address(addr -> addr  // ← Lambda configures nested builder
        .street("123 Main St")
        .city("New York")
        .state("NY")
        .zipCode("10001"))
    .build();
```

---

## **Full-Fledged Real-World Example: E-Commerce Order System**

Let me show you a **complete implementation** with multiple complex objects, collections, and all the techniques:

### **1. Product.java**

```java
public class Product {
    private final String id;
    private final String name;
    private final double price;
    private final String category;
    
    private Product(Builder builder) {
        this.id = builder.id;
        this.name = builder.name;
        this.price = builder.price;
        this.category = builder.category;
    }
    
    public static class Builder {
        private String id;
        private String name;
        private double price;
        private String category;
        
        public Builder id(String id) {
            this.id = id;
            return this;
        }
        
        public Builder name(String name) {
            this.name = name;
            return this;
        }
        
        public Builder price(double price) {
            this.price = price;
            return this;
        }
        
        public Builder category(String category) {
            this.category = category;
            return this;
        }
        
        public Product build() {
            if (id == null) throw new IllegalStateException("Product ID required");
            if (name == null) throw new IllegalStateException("Product name required");
            if (price <= 0) throw new IllegalStateException("Price must be positive");
            return new Product(this);
        }
    }
    
    public static Builder builder() {
        return new Builder();
    }
    
    // Getters
    public String getId() { return id; }
    public String getName() { return name; }
    public double getPrice() { return price; }
    public String getCategory() { return category; }
    
    @Override
    public String toString() {
        return String.format("Product[id=%s, name=%s, price=%.2f, category=%s]", 
            id, name, price, category);
    }
}
```

### **2. OrderItem.java**

```java
public class OrderItem {
    private final Product product;  // ← Complex object
    private final int quantity;
    private final double discount;
    
    private OrderItem(Builder builder) {
        this.product = builder.product;
        this.quantity = builder.quantity;
        this.discount = builder.discount;
    }
    
    public static class Builder {
        private Product product;
        private int quantity = 1;
        private double discount = 0.0;
        
        // Accept Product directly
        public Builder product(Product product) {
            this.product = product;
            return this;
        }
        
        // OR accept Product.Builder
        public Builder product(Product.Builder productBuilder) {
            this.product = productBuilder.build();
            return this;
        }
        
        // OR use Consumer pattern
        public Builder product(Consumer<Product.Builder> productConfig) {
            Product.Builder productBuilder = Product.builder();
            productConfig.accept(productBuilder);
            this.product = productBuilder.build();
            return this;
        }
        
        public Builder quantity(int quantity) {
            this.quantity = quantity;
            return this;
        }
        
        public Builder discount(double discount) {
            this.discount = discount;
            return this;
        }
        
        public OrderItem build() {
            if (product == null) throw new IllegalStateException("Product required");
            if (quantity <= 0) throw new IllegalStateException("Quantity must be positive");
            return new OrderItem(this);
        }
    }
    
    public static Builder builder() {
        return new Builder();
    }
    
    public double getTotalPrice() {
        return product.getPrice() * quantity * (1 - discount);
    }
    
    // Getters
    public Product getProduct() { return product; }
    public int getQuantity() { return quantity; }
    public double getDiscount() { return discount; }
    
    @Override
    public String toString() {
        return String.format("OrderItem[product=%s, quantity=%d, discount=%.2f%%, total=$%.2f]",
            product.getName(), quantity, discount * 100, getTotalPrice());
    }
}
```

### **3. ShippingAddress.java**

```java
public class ShippingAddress {
    private final String recipientName;
    private final String street;
    private final String city;
    private final String state;
    private final String zipCode;
    private final String country;
    private final String phoneNumber;
    
    private ShippingAddress(Builder builder) {
        this.recipientName = builder.recipientName;
        this.street = builder.street;
        this.city = builder.city;
        this.state = builder.state;
        this.zipCode = builder.zipCode;
        this.country = builder.country;
        this.phoneNumber = builder.phoneNumber;
    }
    
    public static class Builder {
        private String recipientName;
        private String street;
        private String city;
        private String state;
        private String zipCode;
        private String country = "USA";  // Default
        private String phoneNumber;
        
        public Builder recipientName(String recipientName) {
            this.recipientName = recipientName;
            return this;
        }
        
        public Builder street(String street) {
            this.street = street;
            return this;
        }
        
        public Builder city(String city) {
            this.city = city;
            return this;
        }
        
        public Builder state(String state) {
            this.state = state;
            return this;
        }
        
        public Builder zipCode(String zipCode) {
            this.zipCode = zipCode;
            return this;
        }
        
        public Builder country(String country) {
            this.country = country;
            return this;
        }
        
        public Builder phoneNumber(String phoneNumber) {
            this.phoneNumber = phoneNumber;
            return this;
        }
        
        public ShippingAddress build() {
            if (recipientName == null) throw new IllegalStateException("Recipient name required");
            if (street == null) throw new IllegalStateException("Street required");
            if (city == null) throw new IllegalStateException("City required");
            if (zipCode == null) throw new IllegalStateException("Zip code required");
            return new ShippingAddress(this);
        }
    }
    
    public static Builder builder() {
        return new Builder();
    }
    
    // Getters
    public String getRecipientName() { return recipientName; }
    public String getStreet() { return street; }
    public String getCity() { return city; }
    public String getState() { return state; }
    public String getZipCode() { return zipCode; }
    public String getCountry() { return country; }
    public String getPhoneNumber() { return phoneNumber; }
    
    @Override
    public String toString() {
        return String.format("%s\n%s\n%s, %s %s\n%s\nPhone: %s",
            recipientName, street, city, state, zipCode, country, phoneNumber);
    }
}
```

### **4. PaymentInfo.java**

```java
public class PaymentInfo {
    private final String cardNumber;
    private final String cardHolderName;
    private final String expiryDate;
    private final String cvv;
    private final String billingAddress;
    
    private PaymentInfo(Builder builder) {
        this.cardNumber = builder.cardNumber;
        this.cardHolderName = builder.cardHolderName;
        this.expiryDate = builder.expiryDate;
        this.cvv = builder.cvv;
        this.billingAddress = builder.billingAddress;
    }
    
    public static class Builder {
        private String cardNumber;
        private String cardHolderName;
        private String expiryDate;
        private String cvv;
        private String billingAddress;
        
        public Builder cardNumber(String cardNumber) {
            this.cardNumber = cardNumber;
            return this;
        }
        
        public Builder cardHolderName(String cardHolderName) {
            this.cardHolderName = cardHolderName;
            return this;
        }
        
        public Builder expiryDate(String expiryDate) {
            this.expiryDate = expiryDate;
            return this;
        }
        
        public Builder cvv(String cvv) {
            this.cvv = cvv;
            return this;
        }
        
        public Builder billingAddress(String billingAddress) {
            this.billingAddress = billingAddress;
            return this;
        }
        
        public PaymentInfo build() {
            if (cardNumber == null) throw new IllegalStateException("Card number required");
            if (cardHolderName == null) throw new IllegalStateException("Cardholder name required");
            // More validation...
            return new PaymentInfo(this);
        }
    }
    
    public static Builder builder() {
        return new Builder();
    }
    
    // Getters (masked for security)
    public String getMaskedCardNumber() {
        return "**** **** **** " + cardNumber.substring(cardNumber.length() - 4);
    }
    
    @Override
    public String toString() {
        return String.format("PaymentInfo[card=%s, holder=%s]",
            getMaskedCardNumber(), cardHolderName);
    }
}
```

### **5. Order.java (The Master Builder)** 🎯

```java
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.function.Consumer;

public class Order {
    private final String orderId;
    private final String customerId;
    private final LocalDateTime orderDate;
    private final List<OrderItem> items;  // ← Collection of complex objects
    private final ShippingAddress shippingAddress;  // ← Complex object
    private final PaymentInfo paymentInfo;  // ← Complex object
    private final String notes;
    private final boolean giftWrap;
    private final String promoCode;
    
    private Order(Builder builder) {
        this.orderId = builder.orderId;
        this.customerId = builder.customerId;
        this.orderDate = builder.orderDate;
        this.items = new ArrayList<>(builder.items);  // Defensive copy
        this.shippingAddress = builder.shippingAddress;
        this.paymentInfo = builder.paymentInfo;
        this.notes = builder.notes;
        this.giftWrap = builder.giftWrap;
        this.promoCode = builder.promoCode;
    }
    
    public static class Builder {
        // Required fields
        private String orderId;
        private String customerId;
        private LocalDateTime orderDate = LocalDateTime.now();
        
        // Complex objects and collections
        private List<OrderItem> items = new ArrayList<>();
        private ShippingAddress shippingAddress;
        private PaymentInfo paymentInfo;
        
        // Optional fields
        private String notes;
        private boolean giftWrap = false;
        private String promoCode;
        
        public Builder orderId(String orderId) {
            this.orderId = orderId;
            return this;
        }
        
        public Builder customerId(String customerId) {
            this.customerId = customerId;
            return this;
        }
        
        public Builder orderDate(LocalDateTime orderDate) {
            this.orderDate = orderDate;
            return this;
        }
        
        // ========== HANDLING COLLECTIONS ==========
        
        // Add single item (pre-built)
        public Builder addItem(OrderItem item) {
            this.items.add(item);
            return this;
        }
        
        // Add single item using builder
        public Builder addItem(OrderItem.Builder itemBuilder) {
            this.items.add(itemBuilder.build());
            return this;
        }
        
        // Add single item using Consumer pattern
        public Builder addItem(Consumer<OrderItem.Builder> itemConfig) {
            OrderItem.Builder itemBuilder = OrderItem.builder();
            itemConfig.accept(itemBuilder);
            this.items.add(itemBuilder.build());
            return this;
        }
        
        // Add multiple items at once
        public Builder items(List<OrderItem> items) {
            this.items.addAll(items);
            return this;
        }
        
        // ========== HANDLING COMPLEX OBJECTS ==========
        
        // Shipping Address - Option 1: Pre-built
        public Builder shippingAddress(ShippingAddress address) {
            this.shippingAddress = address;
            return this;
        }
        
        // Shipping Address - Option 2: Using builder
        public Builder shippingAddress(ShippingAddress.Builder addressBuilder) {
            this.shippingAddress = addressBuilder.build();
            return this;
        }
        
        // Shipping Address - Option 3: Consumer pattern (CLEANEST!)
        public Builder shippingAddress(Consumer<ShippingAddress.Builder> addressConfig) {
            ShippingAddress.Builder addressBuilder = ShippingAddress.builder();
            addressConfig.accept(addressBuilder);
            this.shippingAddress = addressBuilder.build();
            return this;
        }
        
        // Payment Info - Using all 3 approaches
        public Builder paymentInfo(PaymentInfo paymentInfo) {
            this.paymentInfo = paymentInfo;
            return this;
        }
        
        public Builder paymentInfo(PaymentInfo.Builder paymentBuilder) {
            this.paymentInfo = paymentBuilder.build();
            return this;
        }
        
        public Builder paymentInfo(Consumer<PaymentInfo.Builder> paymentConfig) {
            PaymentInfo.Builder paymentBuilder = PaymentInfo.builder();
            paymentConfig.accept(paymentBuilder);
            this.paymentInfo = paymentBuilder.build();
            return this;
        }
        
        // ========== SIMPLE FIELDS ==========
        
        public Builder notes(String notes) {
            this.notes = notes;
            return this;
        }
        
        public Builder giftWrap(boolean giftWrap) {
            this.giftWrap = giftWrap;
            return this;
        }
        
        public Builder giftWrap() {  // Convenient method
            this.giftWrap = true;
            return this;
        }
        
        public Builder promoCode(String promoCode) {
            this.promoCode = promoCode;
            return this;
        }
        
        // ========== BUILD WITH VALIDATION ==========
        
        public Order build() {
            // Validate required fields
            if (orderId == null || orderId.isEmpty()) {
                throw new IllegalStateException("Order ID is required");
            }
            if (customerId == null || customerId.isEmpty()) {
                throw new IllegalStateException("Customer ID is required");
            }
            if (items.isEmpty()) {
                throw new IllegalStateException("Order must have at least one item");
            }
            if (shippingAddress == null) {
                throw new IllegalStateException("Shipping address is required");
            }
            if (paymentInfo == null) {
                throw new IllegalStateException("Payment info is required");
            }
            
            // Business logic validation
            double totalAmount = getTotalAmount();
            if (totalAmount < 0) {
                throw new IllegalStateException("Total amount cannot be negative");
            }
            
            return new Order(this);
        }
        
        // Helper method for validation
        private double getTotalAmount() {
            return items.stream()
                .mapToDouble(OrderItem::getTotalPrice)
                .sum();
        }
    }
    
    public static Builder builder() {
        return new Builder();
    }
    
    // ========== BUSINESS METHODS ==========
    
    public double getSubtotal() {
        return items.stream()
            .mapToDouble(OrderItem::getTotalPrice)
            .sum();
    }
    
    public double getTax() {
        return getSubtotal() * 0.08;  // 8% tax
    }
    
    public double getShippingCost() {
        return giftWrap ? 15.0 : 10.0;
    }
    
    public double getTotal() {
        double total = getSubtotal() + getTax() + getShippingCost();
        
        // Apply promo code discount
        if ("SAVE10".equals(promoCode)) {
            total *= 0.9;  // 10% off
        }
        
        return total;
    }
    
    // Getters
    public String getOrderId() { return orderId; }
    public String getCustomerId() { return customerId; }
    public LocalDateTime getOrderDate() { return orderDate; }
    public List<OrderItem> getItems() { return new ArrayList<>(items); }  // Defensive copy
    public ShippingAddress getShippingAddress() { return shippingAddress; }
    public PaymentInfo getPaymentInfo() { return paymentInfo; }
    public String getNotes() { return notes; }
    public boolean isGiftWrap() { return giftWrap; }
    public String getPromoCode() { return promoCode; }
    
    @Override
    public String toString() {
        StringBuilder sb = new StringBuilder();
        sb.append("=".repeat(60)).append("\n");
        sb.append("ORDER #").append(orderId).append("\n");
        sb.append("=".repeat(60)).append("\n");
        sb.append("Customer ID: ").append(customerId).append("\n");
        sb.append("Order Date: ").append(orderDate).append("\n");
        sb.append("\nITEMS:\n");
        sb.append("-".repeat(60)).append("\n");
        for (OrderItem item : items) {
            sb.append(item).append("\n");
        }
        sb.append("-".repeat(60)).append("\n");
        sb.append(String.format("Subtotal: $%.2f\n", getSubtotal()));
        sb.append(String.format("Tax: $%.2f\n", getTax()));
        sb.append(String.format("Shipping: $%.2f%s\n", getShippingCost(), giftWrap ? " (Gift Wrap)" : ""));
        if (promoCode != null) {
            sb.append("Promo Code: ").append(promoCode).append(" applied\n");
        }
        sb.append(String.format("TOTAL: $%.2f\n", getTotal()));
        sb.append("\nSHIPPING TO:\n");
        sb.append(shippingAddress).append("\n");
        sb.append("\nPAYMENT:\n");
        sb.append(paymentInfo).append("\n");
        if (notes != null) {
            sb.append("\nNOTES: ").append(notes).append("\n");
        }
        sb.append("=".repeat(60)).append("\n");
        return sb.toString();
    }
}
```

---

## **Complete Demo Application**

```java
import java.util.function.Consumer;

public class BuilderPatternDemo {
    
    public static void main(String[] args) {
        
        System.out.println("🛒 E-COMMERCE ORDER BUILDER DEMO\n");
        
        // ========== EXAMPLE 1: Using Pre-Built Objects ==========
        System.out.println("===== EXAMPLE 1: Pre-Built Objects Approach =====\n");
        
        Product laptop = Product.builder()
            .id("PROD-001")
            .name("MacBook Pro")
            .price(2499.99)
            .category("Electronics")
            .build();
        
        Product mouse = Product.builder()
            .id("PROD-002")
            .name("Magic Mouse")
            .price(79.99)
            .category("Accessories")
            .build();
        
        OrderItem item1 = OrderItem.builder()
            .product(laptop)
            .quantity(1)
            .discount(0.05)  // 5% discount
            .build();
        
        OrderItem item2 = OrderItem.builder()
            .product(mouse)
            .quantity(2)
            .build();
        
        ShippingAddress address = ShippingAddress.builder()
            .recipientName("John Doe")
            .street("123 Main Street")
            .city("San Francisco")
            .state("CA")
            .zipCode("94102")
            .phoneNumber("555-1234")
            .build();
        
        PaymentInfo payment = PaymentInfo.builder()
            .cardNumber("4111111111111111")
            .cardHolderName("John Doe")
            .expiryDate("12/25")
            .cvv("123")
            .billingAddress("123 Main Street")
            .build();
        
        Order order1 = Order.builder()
            .orderId("ORD-2025-001")
            .customerId("CUST-12345")
            .addItem(item1)
            .addItem(item2)
            .shippingAddress(address)
            .paymentInfo(payment)
            .giftWrap()
            .promoCode("SAVE10")
            .notes("Please leave at front door")
            .build();
        
        System.out.println(order1);
        
        // ========== EXAMPLE 2: Using Nested Builders (Inline) ==========
        System.out.println("\n===== EXAMPLE 2: Nested Builders Approach =====\n");
        
        Order order2 = Order.builder()
            .orderId("ORD-2025-002")
            .customerId("CUST-67890")
            .addItem(OrderItem.builder()
                .product(Product.builder()
                    .id("PROD-003")
                    .name("iPhone 15 Pro")
                    .price(999.99)
                    .category("Electronics"))
                .quantity(1))
            .addItem(OrderItem.builder()
                .product(Product.builder()
                    .id("PROD-004")
                    .name("AirPods Pro")
                    .price(249.99)
                    .category("Accessories"))
                .quantity(1)
                .discount(0.10))  // 10% discount
            .shippingAddress(ShippingAddress.builder()
                .recipientName("Jane Smith")
                .street("456 Oak Avenue")
                .city("New York")
                .state("NY")
                .zipCode("10001")
                .phoneNumber("555-5678"))
            .paymentInfo(PaymentInfo.builder()
                .cardNumber("5555555555554444")
                .cardHolderName("Jane Smith")
                .expiryDate("06/26")
                .cvv("456")
                .billingAddress("456 Oak Avenue"))
            .build();
        
        System.out.println(order2);
        
        // ========== EXAMPLE 3: Using Consumer Pattern (Most Elegant!) ==========
        System.out.println("\n===== EXAMPLE 3: Consumer Pattern Approach (Lambda Magic!) =====\n");
        
        Order order3 = Order.builder()
            .orderId("ORD-2025-003")
            .customerId("CUST-11111")
            // Add items using lambda configuration
            .addItem(item -> item
                .product(prod -> prod
                    .id("PROD-005")
                    .name("iPad Air")
                    .price(599.99)
                    .category("Tablets"))
                .quantity(2))
            .addItem(item -> item
                .product(prod -> prod
                    .id("PROD-006")
                    .name("Apple Pencil")
                    .price(129.99)
                    .category("Accessories"))
                .quantity(2)
                .discount(0.15))  // 15% discount
            // Configure shipping address with lambda
            .shippingAddress(addr -> addr
                .recipientName("Bob Johnson")
                .street("789 Pine Road")
                .city("Seattle")
                .state("WA")
                .zipCode("98101")
                .phoneNumber("555-9999"))
            // Configure payment with lambda
            .paymentInfo(payment -> payment
                .cardNumber("378282246310005")
                .cardHolderName("Bob Johnson")
                .expiryDate("03/27")
                .cvv("789")
                .billingAddress("789 Pine Road"))
            .giftWrap()
            .notes("Birthday gift - please include card")
            .build();
        
        System.out.println(order3);
        
        // ========== EXAMPLE 4: Mixed Approach (Real-World Scenario) ==========
        System.out.println("\n===== EXAMPLE 4: Mixed Approach =====\n");
        
        // Reuse existing products
        Product existingProduct = Product.builder()
            .id("PROD-007")
            .name("Samsung Galaxy")
            .price(899.99)
            .category("Electronics")
            .build();
        
        Order order4 = Order.builder()
            .orderId("ORD-2025-004")
            .customerId("CUST-22222")
            // Mix of approaches
            .addItem(OrderItem.builder()
                .product(existingProduct)  // Pre-built product
                .quantity(1))
            .addItem(item -> item  // Lambda for new product
                .product(prod -> prod
                    .id("PROD-008")
                    .name("Screen Protector")
                    .price(19.99)
                    .category("Accessories"))
                .quantity(3))
            .shippingAddress(addr -> addr  // Lambda for address
                .recipientName("Alice Williams")
                .street("321 Elm Street")
                .city("Austin")
                .state("TX")
                .zipCode("78701")
                .phoneNumber("555-3333"))
            .paymentInfo(payment -> payment
                .cardNumber("6011111111111117")
                .cardHolderName("Alice Williams")
                .expiryDate("09/25")
                .cvv("321")
                .billingAddress("321 Elm Street"))
            .promoCode("SAVE10")
            .build();
        
        System.out.println(order4);
        
        System.out.println("\n✅ All orders created successfully!");
        System.out.println("\nKey Takeaways:");
        System.out.println("1. ✅ Inner Static Builder pattern handles complex objects elegantly");
        System.out.println("2. ✅ Three approaches: Pre-built, Nested builders, Consumer pattern");
        System.out.println("3. ✅ Consumer pattern (lambdas) is most elegant for nested objects");
        System.out.println("4. ✅ Collections handled with add() methods");
        System.out.println("5. ✅ Validation happens in build() method");
        System.out.println("6. ✅ Objects are immutable and thread-safe");
    }
}
```

---

## **Output Example:**

```
🛒 E-COMMERCE ORDER BUILDER DEMO

===== EXAMPLE 1: Pre-Built Objects Approach =====

============================================================
ORDER #ORD-2025-001
============================================================
Customer ID: CUST-12345
Order Date: 2025-11-05T10:30:45.123

ITEMS:
------------------------------------------------------------
OrderItem[product=MacBook Pro, quantity=1, discount=5.00%, total=$2374.99]
OrderItem[product=Magic Mouse, quantity=2, discount=0.00%, total=$159.98]
------------------------------------------------------------
Subtotal: $2534.97
Tax: $202.80
Shipping: $15.00 (Gift Wrap)
Promo Code: SAVE10 applied
TOTAL: $2476.59

SHIPPING TO:
John Doe
123 Main Street
San Francisco, CA 94102
USA
Phone: 555-1234

PAYMENT:
PaymentInfo[card=**** **** **** 1111, holder=John Doe]

NOTES: Please leave at front door
============================================================
```

---

## **Key Strategies for Complex Objects - Summary**

### **1. Pre-Built Objects**
```java
.shippingAddress(address)  // Pass already-built object
```
**Use when:** Object is reused across multiple orders

### **2. Nested Builders**
```java
.shippingAddress(ShippingAddress.builder()
    .street("123 Main St")
    .city("NYC"))
```
**Use when:** Building inline, straightforward approach

### **3. Consumer Pattern (Lambda)** ⭐ **RECOMMENDED**
```java
.shippingAddress(addr -> addr
    .street("123 Main St")
    .city("NYC"))
```
**Use when:** You want the cleanest, most modern syntax

### **4. Collections**
```java
.addItem(item)           // Single item
.addItem(itemBuilder)    // Using builder
.addItem(item -> {...})  // Using lambda
.items(itemList)         // Multiple items
```

---

## **Pattern to Master - Checklist**

```java
public class MyClass {
    // 1. Final fields (immutable)
    private final Type field;
    
    // 2. Private constructor accepting builder
    private MyClass(Builder builder) {
        this.field = builder.field;
    }
    
    // 3. Static builder() method
    public static Builder builder() {
        return new Builder();
    }
    
    // 4. Inner static Builder class
    public static class Builder {
        // Non-final fields in builder
        private Type field;
        
        // Fluent setters returning 'this'
        public Builder field(Type field) {
            this.field = field;
            return this;
        }
        
        // For complex objects: Accept object, builder, or Consumer
        public Builder complex(ComplexType obj) { ... }
        public Builder complex(ComplexType.Builder builder) { ... }
        public Builder complex(Consumer<ComplexType.Builder> config) { ... }
        
        // For collections: Add methods
        public Builder addItem(Item item) { ... }
        public Builder items(List<Item> items) { ... }
        
        // Build method with validation
        public MyClass build() {
            // Validate
            if (field == null) throw new IllegalStateException("Required");
            return new MyClass(this);
        }
    }
    
    // 5. Getters only (no setters)
    public Type getField() { return field; }
}
```

---
