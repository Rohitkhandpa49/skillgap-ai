import java.util.Scanner;
public class Quadratic {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);

        System.out.println("Enter a: ");
        double a = sc.nextDouble();

        System.out.println("Enter b: ");
        double b = sc.nextDouble();

        System.out.println("Enter c: ");
        double c = sc.nextDouble();

        double D = b * b - 4*a*c;

        if(D > 0) {
            double root1 = (-b + Math.sqrt(D)) / (2*a);
            double root2 = (-b - Math.sqrt(D)) / (2*a);

            System.out.println("Roots are: " + root1 + " and " + root2);
        } else if(D == 0) {
            double root = -b / (2*a);
            
            System.out.println("Equal root is: " + root);
        } else {
            System.out.println("No real solutions. ");
        }
        sc.close();
    }
    
}
