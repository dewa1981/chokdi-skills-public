import com.healthmarketscience.jackcess.*;
import com.healthmarketscience.jackcess.crypt.CryptCodecProvider;
import java.io.*;
import java.util.*;

public class AccessDump {
  public static void main(String[] a) throws Exception {
    File f = new File(a[0]);
    String pwd = a[1];
    Database db = new DatabaseBuilder(f)
        .setReadOnly(true)
        .setCodecProvider(new CryptCodecProvider(pwd))
        .open();
    System.out.println("DB_OK\t" + f.getName());
    for (String tn : db.getTableNames()) {
      Table t = db.getTable(tn);
      List<? extends Column> cols = t.getColumns();
      StringBuilder h = new StringBuilder("HEADER");
      for (Column c : cols) h.append('\t').append(c.getName());
      System.out.println("TABLE\t" + tn);
      System.out.println(h);
      Cursor cur = t.getDefaultCursor();
        while (cur.moveToNextRow()) {
          Row row = cur.getCurrentRow();
          StringBuilder sb = new StringBuilder("ROW");
          for (Column c : cols) {
            Object v = row.get(c.getName());
            sb.append('\t').append(fmt(v));
          }
          System.out.println(sb);
        }
    }
    System.out.println("DONE");
  }
  static String fmt(Object v) {
    if (v == null) return "";
    if (v instanceof byte[]) {
      StringBuilder sb = new StringBuilder("0x");
      for (byte x : (byte[]) v) sb.append(String.format("%02x", x));
      return sb.toString();
    }
    return String.valueOf(v).replace('\t', ' ').replace('\n', ' ').replace('\r', ' ');
  }
}
