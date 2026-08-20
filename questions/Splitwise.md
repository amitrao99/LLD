```Java


import java.util.*;
import java.util.stream.Collectors;

// ============================================================
// Entities
// ============================================================
record User (String id){}

record Group (String id){}


interface UserRepository {
    boolean exists(User user);

    void addUser(User user);

    void removeUser(User user);
}


class UserRepositoryImpl implements UserRepository {
    private final Set<User> userSet = new HashSet<>();

    @Override
    public boolean exists(User user) {
        return userSet.contains(user);
    }

    @Override
    public void addUser(User user) {
        if (exists(user)) {
            throw new IllegalStateException("User already exists");
        }
        userSet.add(user);
    }

    @Override
    public void removeUser(User user) {
        if (!exists(user)) {
            throw new IllegalStateException("User does not exist");
        }
        userSet.remove(user);
    }
}


interface GroupRepository {
    boolean exists(Group group);

    void addGroup(Group group);

    void removeGroup(Group group);
}


class GroupRepositoryImpl implements GroupRepository {
    private final Set<Group> groupSet = new HashSet<>();

    @Override
    public boolean exists(Group group) {
        return groupSet.contains(group);
    }

    @Override
    public void addGroup(Group group) {
        if (exists(group)) {
            throw new IllegalStateException("Group already exists");
        }
        groupSet.add(group);
    }

    @Override
    public void removeGroup(Group group) {
        if (!exists(group)) {
            throw new IllegalStateException("Group does not exist");
        }
        groupSet.remove(group);
    }
}


interface Record {
    String describe();
}

record ExpenseRecord(User payer, int amount, String description) implements Record {
    @Override
    public String describe() {
        return payer.getId() + " paid " + amount + " for " + description;
    }
}

record PaymentRecord(User payer, User payee, int amount, String description) implements Record {
    @Override
    public String describe() {
        return payer.getId() + " paid " + payee.getId() + " " + amount;
    }
}


interface Ledger {
    void process(PaymentRecord payment);

    int owes(String debtor, String creditor);

    boolean isZero();

    boolean isZeroFor(String userId);

    void dropParticipant(String userId);

    Map<String, Map<String, Integer>> view();
}

class LedgerImpl implements Ledger {
    private final Map<String, Map<String, Integer>> balanceLedger;

    public LedgerImpl() {
        this.balanceLedger = new HashMap<>();
    }

    @Override
    public void process(PaymentRecord payment) {
        String payer = payment.getPayer().getId();
        String payee = payment.getPayee().getId();
        int amount = payment.getAmount();

        // Payer handed money over, so the payer owes the payee less.
        add(payer, payee, -amount);
        add(payee, payer, amount);
    }

    private void add(String a, String b, int delta) {
        Map<String, Integer> row = balanceLedger.get(a);
        if (row == null) {
            row = new HashMap<>();
            balanceLedger.put(a, row);
        }

        Integer current = row.get(b);
        if (current == null) {
            current = 0;
        }

        row.put(b, current + delta);
    }

    @Override
    public int owes(String debtor, String creditor) {
        Map<String, Integer> row = balanceLedger.get(debtor);
        if (row == null) {
            return 0;
        }

        Integer value = row.get(creditor);
        if (value == null) {
            return 0;
        }

        return value;
    }

    @Override
    public boolean isZero() {
        for (Map<String, Integer> row : balanceLedger.values()) {
            for (int value : row.values()) {
                if (value != 0) {
                    return false;
                }
            }
        }
        return true;
    }

    @Override
    public boolean isZeroFor(String userId) {
        Map<String, Integer> row = balanceLedger.get(userId);
        if (row == null) {
            return true;
        }

        for (int value : row.values()) {
            if (value != 0) {
                return false;
            }
        }
        return true;
    }

    @Override
    public void dropParticipant(String userId) {
        balanceLedger.remove(userId); // their row

        for (Map<String, Integer> row : balanceLedger.values()) {
            row.remove(userId); // their column
        }
    }

    @Override
    public Map<String, Map<String, Integer>> view() {
        return balanceLedger;
    }
}


interface ExpenseStrategy {
    List<PaymentRecord> split(ExpenseRecord expense, Set<User> members);
}

class EqualSplit implements ExpenseStrategy {
    @Override
    public List<PaymentRecord> split(ExpenseRecord expense, Set<User> members) {
        if (members.isEmpty()) {
            throw new IllegalStateException("Group has no members");
        }

        int n = members.size();
        int share = expense.getAmount() / n;
        int remainder = expense.getAmount() % n;

        List<PaymentRecord> payments = new ArrayList<>();
        int i = 0;

        for (User member : members) {
            int owed = share;
            if (i < remainder) {
                owed = owed + 1; // spread leftover units over the first few
            }
            i++;

            if (member.equals(expense.getPayer())) {
                continue; // payer's own share cancels against itself
            }

            if (owed > 0) {
                payments.add(new PaymentRecord(expense.getPayer(), member, owed));
            }
        }

        return payments;
    }
}


// ============================================================
// GroupState — everything true WITHIN one group.
// Owns its invariants; nobody mutates it from outside.
// ============================================================

class GroupState {
    private final Group group;
    private final Set<User> users;
    private final Ledger ledger;
    private final List<Record> history;

    public GroupState(Group group, Ledger ledger) {
        this.group = group;
        this.users = new HashSet<>();
        this.ledger = ledger;
        this.history = new ArrayList<>();
    }

    public void addUser(User user) {
        if (!users.add(user)) {
            throw new IllegalStateException("Already a member: " + user.getId());
        }
    }

    public void removeUser(User user) {
        requireMember(user);
        if (!ledger.isZeroFor(user.getId())) {
            throw new IllegalStateException("Outstanding balances: " + user.getId());
        }
        ledger.dropParticipant(user.getId());
        users.remove(user);
    }

    public void addExpense(ExpenseRecord expense, ExpenseStrategy strategy) {
        requireMember(expense.getPayer());
        strategy.split(expense, users).forEach(ledger::process);
        history.add(expense);
    }

    public void addPayment(PaymentRecord payment) {
        requireMember(payment.getPayer());
        requireMember(payment.getPayee());
        ledger.process(payment);
        history.add(payment);
    }

    // TODO: settle-up. Read everything this user owes, emit one
    // PaymentRecord per creditor, feed them through addPayment.
    // Materialise the list before processing — addPayment mutates
    // the map you would otherwise be iterating.
    public void settleUp(User user) {
        throw new UnsupportedOperationException("Not implemented yet");
    }

    public boolean isSettled() {
        return ledger.isZero();
    }

    public int owes(User debtor, User creditor) {
        return ledger.owes(debtor.getId(), creditor.getId());
    }

    public Group getGroup() {
        return group;
    }

    public Set<User> getUsers() {
        return Collections.unmodifiableSet(users);
    }

    public List<Record> getHistory() {
        return Collections.unmodifiableList(history);
    }

    public Ledger getLedger() {
        return ledger;
    }

    private void requireMember(User user) {
        if (!users.contains(user)) {
            throw new IllegalArgumentException("Not a member: " + user.getId());
        }
    }
}


// ============================================================
// GroupManager — lifecycle and cross-group concerns.
// Delegates everything intra-group to GroupState.
// ============================================================

class GroupManager {
    private final GroupRepository groupRepository;
    private final UserRepository userRepository;
    private final Map<String, GroupState> groupMap;

    public GroupManager(GroupRepository groupRepository, UserRepository userRepository) {
        this.groupRepository = groupRepository;
        this.userRepository = userRepository;
        this.groupMap = new HashMap<>();
    }

    public void addGroup(Group group) {
        groupRepository.addGroup(group);
        groupMap.put(group.getId(), new GroupState(group, new LedgerImpl()));
    }

    public void addUserToGroup(User user, Group group) {
        if (!userRepository.exists(user)) {
            throw new IllegalArgumentException("No such user: " + user.getId());
        }
        require(group).addUser(user);
    }

    public void removeUserFromGroup(User user, Group group) {
        require(group).removeUser(user);
    }

    public void addExpense(Group group, ExpenseRecord expense, ExpenseStrategy strategy) {
        require(group).addExpense(expense, strategy);
    }

    public void addPayment(Group group, PaymentRecord payment) {
        require(group).addPayment(payment);
    }

    public boolean settled(Group group) {
        return require(group).isSettled();
    }

    public void removeGroup(Group group) {
        GroupState state = require(group);
        if (!state.isSettled()) {
            throw new IllegalStateException("Group is not settled");
        }
        groupMap.remove(group.getId());
        groupRepository.removeGroup(group);
    }

    public GroupState stateOf(Group group) {
        return require(group);
    }

    private GroupState require(Group group) {
        GroupState state = groupMap.get(group.getId());
        if (state == null) {
            throw new IllegalArgumentException("No such group: " + group.getId());
        }
        return state;
    }
}


class Splitwise {
    private final UserRepository userRepository;
    private final GroupManager groupManager;
    private final ExpenseStrategy defaultStrategy;

    public Splitwise() {
        this.userRepository = new UserRepositoryImpl();
        this.groupManager = new GroupManager(new GroupRepositoryImpl(), userRepository);
        this.defaultStrategy = new EqualSplit();
    }

    public void addUser(User user) {
        userRepository.addUser(user);
    }

    public void createGroup(Group group) {
        groupManager.addGroup(group);
    }

    public void addUserToGroup(User user, Group group) {
        groupManager.addUserToGroup(user, group);
    }

    public void addExpense(Group group, User payer, int amount, String description) {
        groupManager.addExpense(
                group,
                new ExpenseRecord(payer, amount, description),
                defaultStrategy
        );
    }

    public void recordPayment(Group group, User payer, User payee, int amount) {
        groupManager.addPayment(group, new PaymentRecord(payer, payee, amount));
    }

    public int owes(Group group, User debtor, User creditor) {
        return groupManager.stateOf(group).owes(debtor, creditor);
    }

    public boolean settled(Group group) {
        return groupManager.settled(group);
    }

    public List<Record> history(Group group) {
        return groupManager.stateOf(group).getHistory();
    }
}


class Main {
    public static void main(String[] args) {
        Splitwise app = new Splitwise();

        User alice = new User("alice");
        User bob = new User("bob");
        User carol = new User("carol");
        app.addUser(alice);
        app.addUser(bob);
        app.addUser(carol);

        Group trip = new Group("trip");
        app.createGroup(trip);
        app.addUserToGroup(alice, trip);
        app.addUserToGroup(bob, trip);
        app.addUserToGroup(carol, trip);

        // Alice fronts 300 for dinner -> Bob and Carol each owe her 100.
        app.addExpense(trip, alice, 300, "Dinner");
        System.out.println("bob owes alice   : " + app.owes(trip, bob, alice));   // 100
        System.out.println("carol owes alice : " + app.owes(trip, carol, alice)); // 100
        System.out.println("alice owes bob   : " + app.owes(trip, alice, bob));   // -100
        System.out.println("settled          : " + app.settled(trip));            // false

        // Bob pays Alice back.
        app.recordPayment(trip, bob, alice, 100);
        System.out.println("bob owes alice   : " + app.owes(trip, bob, alice));   // 0
        System.out.println("settled          : " + app.settled(trip));            // false

        // Carol pays too.
        app.recordPayment(trip, carol, alice, 100);
        System.out.println("settled          : " + app.settled(trip));            // true

        System.out.println("\nHistory:");
        app.history(trip).forEach(r -> System.out.println("  " + r.describe()));
    }
}
```