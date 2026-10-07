class Rectangle {

    double width, length, area;
    String color;

    void set_length(double l) {
        length = l;
    }

    void set_width(double w) {
        width = w;
    }

    void set_color(String c) {
        color = c;
    }

    void find_area() {
        area = length * width;
    }
}

public class RectangleTest {

    public static void main(String[] args) {

        Rectangle r1 = new Rectangle();
        Rectangle r2 = new Rectangle();

        r1.set_length(5);
        r1.set_width(4);
        r1.set_color("Red");
        r1.find_area();

        r2.set_length(4);
        r2.set_width(5);
        r2.set_color("Red");
        r2.find_area();

        if (r1.area == r2.area &&
            r1.color.equals(r2.color))

            System.out.println("Matching Rectangles");

        else

            System.out.println("Non-Matching Rectangles");
    }
}