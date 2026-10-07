import java.util.Scanner;

public class fibonacci {

    // Recursive method to find nth Fibonacci number
    static int recursiveFib(int n) {
        if (n <= 1)
            return n;

        return recursiveFib(n - 1) + recursiveFib(n - 2);
    }

    // Non-recursive method to find nth Fibonacci number
    static int nonRecursiveFib(int n) {

        int a = 0;
        int b = 1;
        int c;

        if (n == 0)
            return a;

        if (n == 1)
            return b;

        for (int i = 2; i <= n; i++) {
            c = a + b;
            a = b;
            b = c;
        }

        return b;
    }

    static void printRecursiveSeries(int n) {
        for (int i = 0; i <= n; i++) {
            System.out.print(recursiveFib(i) + " ");
        }
        System.out.println();
    }

    static void printNonRecursiveSeries(int n) {

        int a = 0, b = 1, c;

        if (n >= 0)
            System.out.print(a + " ");

        if (n >= 1)
            System.out.print(b + " ");

        for (int i = 2; i <= n; i++) {
            c = a + b;
            System.out.print(c + " ");
            a = b;
            b = c;
        }

        System.out.println();
    }

    public static void main(String[] args) {

        Scanner sc = new Scanner(System.in);

        System.out.print("Enter n: ");
        int n = sc.nextInt();

        System.out.println("\nRecursive Fibonacci Series:");
        printRecursiveSeries(n);

        System.out.println("Non-Recursive Fibonacci Series:");
        printNonRecursiveSeries(n);

        int recursiveFibNo = recursiveFib(n);
        int nonRecursiveFibNo = nonRecursiveFib(n);

        System.out.println("\nRecursive Fibonacci (" + n + "th term): " + recursiveFibNo);
        System.out.println("Non-Recursive Fibonacci (" + n + "th term): " + nonRecursiveFibNo);

        sc.close();
    }
}