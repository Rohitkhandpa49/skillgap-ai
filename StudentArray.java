public class StudentArray {

    public static void main(String[] args) {

        String name[] = new String[10];
        int roll[] = new int[10];

        try {

            for (int i = 0; i <= 10; i++) {

                name[i] = "Student" + i;
                roll[i] = i + 1;

                System.out.println(name[i] + " " + roll[i]);
            }

        } catch (ArrayIndexOutOfBoundsException e) {

            System.out.println("Array Index Out Of Bounds Exception Handled");
        }
    }
}