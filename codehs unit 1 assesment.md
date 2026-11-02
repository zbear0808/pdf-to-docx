codehs unit 1 assesment


multiple choice 


Name: 
Date: 
Section: 
CodeHS
Using Objects and Methods -- Unit MCQ

Which of the following pairs of declarations will cause an error message?
1.

double x = 17.4;
int y = x;

double x = 17.4;
int y = (int) x;

int x = 17;
double y = x;

    None of them will result in an error message.

    1 only

    2 only

    1 and 3 only

What is printed as a result of executing this code segment?

System.out.println("2" + 3);

    23

    5

    2 + 3

    “2”3

Consider the following code segment.

double answer = 18 / 5;
System.out.println("18/5 = " + answer);

The output is:

18/5 = 3.0

The programmer intends the output to be:

18/5 = 3.6

Which of the following replacements for the first line of code will NOT fix the problem?

    double answer = (double) 18 / 5;

    double answer = 18 / (double) 5;

    double answer = 18 / 5.0;

    double answer = (double) (18 / 5);

A student has created a Car class. The class contains the following instance variables:

    A String variable called color to represent the color of the car.
    An int variable called year to represent the year the car was made.
    A String variable called make to represent the manufacturer of the car.
    A String variable called model to represent the model of the car.

The variable vehicle will be declared as a reference of type Car:

Car vehicle = new Car("yellow", 2010, "Toyota", "Camry");

Which of the following descriptions is accurate?

    An instance of the vehicle class is Car.

    An instance of the Car object is vehicle.

    An attribute of the year object is int.

    An attribute of the vehicle object is color.

Which of the following variable declarations is invalid?

    int num = 5.0;

    double value = 7.5;

    String name = "AP Computer Science";

    boolean on = true;

Consider the class below:

public class Bee
{
    public void buzz()
    {
        System.out.print("Buzz ");
    }

    public void pollinate()
    {
        System.out.print("Flowers");
    }

    public void work()
    {
        buzz();
        pollinate();
    }

    /* Constructors not shown */
}

Which of the following code segments, if located in a method in a class other than Bee, will cause the message “Buzz Flowers” to be printed?

Bee.buzz();
Bee.pollinate();

Bee.work();

Bee b = new Bee();
b.work();

    1 only

    1 and 2 only

    3 only

    1, 2, and 3

Consider the following code segment:

String oldStr = "ABCDEF";
String newStr = oldStr.substring(1, 3) + oldStr.substring(4);
System.out.println(newStr);

What is the output of the code segment?

    ABCD

    BCDE

    BCEF

    BCDEF

Given the following code, what will be printed?

int a = 5;
a += 3;
a *= 2;
a -= 4;
System.out.println(a);

    6

    8

    10

    12

Consider the following utility class, defined in its own file:

public class MathUtils
{
    public static int square(int x)
    {
        return x * x;
    }

    public static int cube(int x)
    {
        return x * x * x;
    }
}

Which of the following code segments, if located in a method in a class other than MathUtils, will correctly compute and print

16 27

to the console?

    int a = new MathUtils(4).square();
    int b = new MathUtils(3).cube();
    System.out.println(a + " " + b);

    int a = MathUtils.square(4);
    int b = MathUtils.cube(3);
    System.out.println(a + " " + b);

    MathUtils utils = MathUtils();
    int a = utils.square(4);
    int b = utils.cube(3);
    System.out.println(a + " " + b);

    int a = square(4);
    int b = cube(3);
    System.out.println(a + " " + b);

Consider the following attempts at method overloading.

public class Overload
{
    public int average(int x, int y)
    { /* implementation not shown */ }

    public int average(int value1, int value2)
    { /* implementation not shown */ }
}

public class Overload
{
    public int average(int x, int y)
    { /* implementation not shown */ }

    public int average(int x, int y, int z)
    { /* implementation not shown */ }
}

public class Overload
{
    public int average(int x, int y)
    { /* implementation not shown */ }

    public int average(double x, double y)
    { /* implementation not shown */ }
}

Which of the attempts at method overloading will compile without error?

    2 only

    3 only

    2 and 3 only

    1, 2, and 3

Given the following method signature, what is the return type of the method?

public static void myMethod(int a, double b);

    void

    int

    double

    static

Given the following class definition:

public class Book
{
    String bookTitle;
    String bookAuthor;

    public Book(String title, String author)
    {
        bookTitle = title;
        bookAuthor = author;
    }
}

Which of the following is the correct way to create an instance of the Book class?

    Book myBook = new Book();

    Book myBook = new Book("1984", "George Orwell");

    Book myBook;

    myBook = new Book("To Kill a Mockingbird", "Harper Lee");

You’re building an air-quality monitoring app with the class below:

public class AirQuality
{
    private int readingId;
    private double pm25Level;
    private boolean alert;

    public AirQuality(int id, double level)
    {
        readingId = id;
        pm25Level = level;
        alert = false;
    }

    public AirQuality(int id)
    {
        readingId = id;
        pm25Level = 12.0;
        alert = false;
    }
}

Which of the following snippets, when in a class other than AirQuality, will successfully create a new AirQuality object?

AirQuality readingOne = new AirQuality(1001, 35.4);

AirQuality readingTwo = new AirQuality(1002);

int idCode = 1003;
double levelVal = 50.2;
AirQuality readingThree = new AirQuality(idCode, levelVal);

    1 only

    1 and 2 only

    1, 2, and 3

    None of these will compile, because Java classes can only have a single constructor, yet this class defines two.

Assuming the following method is defined in the same class:

public static int addNumbers(int x, int y)
{ /* implementation not shown */ }

Which of these statements, when placed inside a method in the same class, correctly calls addNumbers?

    addNumbers();

    addNumbers(1.0, 6.0);

    addNumbers(3, 4);

    main.addNumbers(3, 4);

Consider the following code segment.

String firstName = "John";
String lastName = "Doe";
String greeting = "Hello, ";

Which of the following statements correctly creates a string that concatenates greeting, firstName, and lastName into the sentence “Hello, John Doe”?

    String message = greeting + firstName + " " + lastName;

    String message = greeting + firstName + lastName;

    String message = greeting + " " + lastName + " " + firstName;

    String message = greeting.concat(firstName).concat(lastName);

Consider the following code segment.

int x = 16;
double result = Math.sqrt(x) + Math.pow(2, 3);

What will be the value of result after the code executes?

    5.0

    8.0

    12.0

    20.0

Which of the following is a valid comment in Java?

    /* This is a comment */

    

    # This is a comment

    "// This is a comment"

What is the output of the following code?

String first = "Advanced";
String second = "Placement";
String result = first.substring(0, 2) + second.length() + first.indexOf('v');
System.out.println(result);

    Ad93

    Ad92

    Advanced92

    Ad82

Consider the following code snippet:

int num1 = (int)(Math.random() * 5) + 10;
int num2 = (int)(Math.random() * 4) + 20;
System.out.println("(" + num1 + ", " + num2 + ")");

Which of the following could legitimately appear on the console when this runs?

    (11, 19)

    (14, 24)

    (9, 21)

    (12, 22)

What will the following code print?

System.out.print("\\* This is not\n a comment *\\");

    \* This is not a comment *\

    * This is not
     a comment *

    \\* This is not
     a comment *\\

    \* This is not
     a comment *\





frq 1

Scenario:

You are tasked with implementing an `Account` class to represent an individual’s bank account. Each `Account` object stores the name of the account holder and the balance of the account. A partial declaration of the `Account` class is shown in the editor. An additional class, `AccountRunner`, is provided at the bottom of the editor to simulate account creations. You can assume that these two classes exist in their own files of the same name.

### Task:

**Complete the following in the `Account` class:**

**(a)** The two overloaded constructors. The first initializes the two instance variables with the two parameters, `userName` and `accountBalance`. The second initializes the just the `name` value with the parameter, and then sets the `balance` to a value of `0.0`.

**(b)** The deposit and withdraw methods. These two methods should increase and decrease the account’s balance by the specified `amount` parameter.

**In the `AccountRunner` class (in the bottom of the editor):**

**(c)** Create two new account objects, using each of the two overloaded constructors in the `Account` class. You can use any appropriate values you’d like as the arguments. Then call the `deposit` and `withdraw` methods on each of the two accounts, again using any appropriate values as the arguments.

public class Account
{
    private String name;
    private double balance;

    /**
     * Creates an account with a user's name and
     * starting balance.
     */
    public Account(String userName, double accountBalance)
    {
        /* to be implemented in part (a) */
    }

    /**
     * Creates an account with just the user's name
     * and sets the account balance to a default value
     * of 0.0
     */
    public Account(String userName)
    {
        /* to be implemented in part (a) */
    }

    /**
     * Adds the specified amount to the account balance.
     */
    public void deposit(double amount)
    {
        /* to be implemented in part (b) */
    }

    /**
     * Removes the specified amount from the account balance.
     */
    public void withdraw(double amount)
    {
        /* to be implemented in part (b) */
    }
}

=============================================================

public class AccountRunner
{
    public static void main(String[] args)
    {
        /* to be implemented in part (c) */
    }
}




FRQ 2



### Scenario

This program uses the utility methods in `StudentUtil` class to process information about students and their performance in school. You will complete three methods that calculate grade percentages, generate standardized email addresses, and produce student IDs based on provided data. These methods will be tested using the `StudentRunner` class.

You are provided with a partial declaration of the `StudentUtil` class and the `StudentRunner` class in the editor (you can assume that these two classes exist in their own files of the same name). You will complete the methods and write code to test them.

### Task

**In the StudentUtil class:**

**(a)** Write the `calcPercentage` method. The method returns the percentage score a student earned on an assignment. The method calculates the ratio of earned points to total possible points and returns this value as a number between 0.0 and 100.0. The return value must be of type double.

For example:

* inputs of 75 and 100 should return 75.0
* inputs of 35 and 40 should returns 87.5

**(b)** Write the `genStudentEmail` method. The method returns a string that contains an email address for a student using the format first.lastNN@school.edu. NN is the combined length of the first and last names. *Optional - the first and last names can be converted to lowercase (see note below for methods).*

For example:

* inputs “Tina” and “Lee” should return “Tina.Lee7@school.edu” (optional - lowercase “tina” and “lee”)
* inputs “Jamal” and “Washington” should return “Jamal.Washington15@school.edu” (optional - lowercase “jamal” and “washington”).

**(c)** Write the `genStudentID` method. The method generates a six-character student ID. The ID consists of the first three letters of `lastName`, followed by a random three-digit number between 100 and 999, inclusive. *Optional - the first three letters of `lastName` can be all uppercase (see note below for methods).*

For example:

* input “Garcia” could return “Gar173” (optional - uppercase “GAR173”)
* input “Nguyen” could return “Ngu482” (optional - uppercase “NGU482”)

Note that any valid random three-digit number may be returned, and multiple outputs are acceptable.

**In the StudentRunner class:**

**(d)** Write statements to test all three class methods in `StudentUtil`. Print the results to the console. You may store the return values in variables or print them directly.

Your output must include:

* The email address generated from genStudentEmail
* The student ID generated from genStudentID
* The percentage score from calcPercentage

Use the test data provided in the starter code in your method calls.

---

`String` methods like `toLowerCase` and `toUpperCase` are useful for formatting text in your program, making it easier to compare, store, and display information in different contexts.

* `toLowerCase` - returns the value of the string converted to lower case. For example, if variable `word` equals `"Test"`, then `word.toLowerCase();` returns “test”.
* `toUpperCase` - returns the value of the string converted to upper case. For example, if variable `word` equals `"Test"`, then `word.toUpperCase();` returns “TEST”.

public class StudentUtil
{
    /**
     * Calculates and returns the student's grade percentage.
     * earnedPoints – points the student earned
     * totalPoints  – total points possible (must be > 0)
     * The result is a value from 0.0 to 100.0.
     */
    public static double calcPercentage(int earnedPoints, int totalPoints)
    {
        /* to be implemented in part (a) */
    }

    /**
     * Builds an email address in the form
     * first.lastNN@school.edu, where first and last are the
     * the names (optionally lowercase) and NN is the combined
     * length of the two names.
     */
    public static String genStudentEmail(String firstName, String lastName)
    {
        /* to be implemented in part (b) */
    }

    /**
     * Creates a six-character student ID made up of the first three
     * letters of lastName (optionally uppercase) followed by a random
     * three-digit number from 100 to 999 inclusive.
     * Precondition: lastName has at least three characters.
     */
    public static String genStudentID(String lastName)
    {
        /* to be implemented in part (c) */
    }
}

========================================================

public class StudentRunner
{
    public static void main(String[] args)
    {
        // Student information to test methods
        String studentFirst = "Gabbi";
        String studentLast = "Martinez";
        int earned = 340;
        int possible = 400;

        /* to be implemented in part (d) */

    }
}
