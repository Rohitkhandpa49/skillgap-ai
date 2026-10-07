interface Student {
    void Display_Grade();
    void Attendence();

class PG_Students implements Student {

    public void Display_Grade() {
        System.out.println("PG Grade: B");

    }
    public void Attendence() {
        System.out.println("PG Attendence: 90%");
    }
    
}
class UG_Students implements Student {
    public void Display_Grade() {
        System.out.println("UG Grade: C");
    }
    public void Attendence() {
        System.out.println("UG Attendence: 80%");
    }
}
    public class Studentfinal {
        public static void main(String[] args) {
            PG_Students pg = new PG_Students();
            UG_Students ug = new UG_Students();

            pg.Display_Grade();
            pg.Attendence();

            ug.Display_Grade();
            ug.Attendence();
        }
    }
}
