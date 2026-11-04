package com.streetceo.app;

import android.app.Activity;
import android.content.ActivityNotFoundException;
import android.content.ClipData;
import android.content.ContentValues;
import android.os.Build;
import android.os.Environment;
import android.provider.MediaStore;
import android.util.Base64;
import androidx.activity.result.ActivityResult;
import com.getcapacitor.annotation.ActivityCallback;
import android.content.Intent;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.RectF;
import android.graphics.Typeface;
import android.graphics.pdf.PdfDocument;
import android.net.Uri;
import com.getcapacitor.JSArray;
import com.getcapacitor.JSObject;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;
import org.json.JSONObject;
import java.io.File;
import java.io.FileOutputStream;
import java.io.FileInputStream;
import java.io.OutputStream;
import java.nio.charset.StandardCharsets;
import java.util.UUID;
import java.util.ArrayList;
import java.util.List;

/** User-initiated report files only; no arbitrary paths, HTML, URLs or storage permissions. */
@CapacitorPlugin(name = "StreetReportExport")
public class StreetReportExportPlugin extends Plugin {
    private File target(PluginCall call, String extension) throws Exception {
        String name = call.getString("filename", "");
        boolean businessPlanPdf = extension.equals("pdf") && name.equals("street-ceo-business-plan")
                && "Business plan".equals(call.getString("title", ""));
        if (!businessPlanPdf && !name.matches("street-ceo-(sales|profit)-[0-9]{4}-[0-9]{2}-[0-9]{2}-to-[0-9]{4}-[0-9]{2}-[0-9]{2}")) {
            throw new IllegalArgumentException("Invalid export filename");
        }
        File directory = new File(getContext().getCacheDir(), "report-exports").getCanonicalFile();
        if (!directory.exists() && !directory.mkdirs()) throw new IllegalStateException();
        File file = new File(directory, name + "-" + UUID.randomUUID() + "." + extension).getCanonicalFile();
        if (!directory.equals(file.getParentFile())) throw new IllegalArgumentException();
        return file;
    }
    private void copyReport(File file, Uri uri) throws Exception {
        try (FileInputStream input = new FileInputStream(file);
             OutputStream output = getContext().getContentResolver().openOutputStream(uri)) {
            if (output == null) throw new IllegalStateException("No download output stream");
            byte[] buffer = new byte[8192];
            int size;
            while ((size = input.read(buffer)) != -1) output.write(buffer, 0, size);
        }
    }

    private void openDownload(PluginCall call, Uri uri, String mime) {
        getActivity().runOnUiThread(() -> {
            boolean opened = false;
            Intent view = new Intent(Intent.ACTION_VIEW).setDataAndType(uri, mime);
            view.setClipData(ClipData.newRawUri("Street CEO report", uri));
            view.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
            try {
                getActivity().startActivity(view);
                opened = true;
            } catch (ActivityNotFoundException | SecurityException unavailable) {
                // The saved file remains available through the Files app.
            }
            JSObject result = new JSObject();
            result.put("opened", opened);
            result.put("savedToDownloads", Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q);
            call.resolve(result);
        });
    }

    private void saveReport(PluginCall call, File file, String mime, String extension) throws Exception {
        String filename = call.getString("filename", "") + "." + extension;
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.Q) {
            Intent create = new Intent(Intent.ACTION_CREATE_DOCUMENT)
                    .addCategory(Intent.CATEGORY_OPENABLE).setType(mime)
                    .putExtra(Intent.EXTRA_TITLE, filename);
            call.getData().put("pendingFile", file.getName());
            call.getData().put("pendingMime", mime);
            startActivityForResult(call, create, "documentCreated");
            return;
        }

        ContentValues values = new ContentValues();
        values.put(MediaStore.Downloads.DISPLAY_NAME, filename);
        values.put(MediaStore.Downloads.MIME_TYPE, mime);
        values.put(MediaStore.Downloads.RELATIVE_PATH, Environment.DIRECTORY_DOWNLOADS);
        values.put(MediaStore.Downloads.IS_PENDING, 1);
        Uri uri = getContext().getContentResolver().insert(MediaStore.Downloads.EXTERNAL_CONTENT_URI, values);
        if (uri == null) throw new IllegalStateException("Could not create download");
        try {
            copyReport(file, uri);
            values.clear();
            values.put(MediaStore.Downloads.IS_PENDING, 0);
            if (getContext().getContentResolver().update(uri, values, null, null) != 1) {
                throw new IllegalStateException("Could not publish download");
            }
        } catch (Exception failure) {
            getContext().getContentResolver().delete(uri, null, null);
            throw failure;
        } finally {
            file.delete();
        }
        openDownload(call, uri, mime);
    }

    @ActivityCallback
    private void documentCreated(PluginCall call, ActivityResult result) {
        if (call == null) return;
        String name = call.getString("pendingFile", "");
        if (!name.matches("street-ceo-[a-z0-9-]+\\.(csv|pdf|xlsx)")) {
            call.reject("The pending report could not be found.");
            return;
        }
        File file = new File(new File(getContext().getCacheDir(), "report-exports"), name);
        try {
            Intent data = result.getData();
            if (result.getResultCode() != Activity.RESULT_OK || data == null || data.getData() == null) {
                call.reject("Download cancelled.");
                return;
            }
            Uri uri = data.getData();
            copyReport(file, uri);
            openDownload(call, uri, call.getString("pendingMime", "application/octet-stream"));
        } catch (Exception failure) {
            call.reject("Could not save the report. Try again.");
        } finally {
            file.delete();
        }
    }
    @PluginMethod public void downloadCsv(PluginCall call) {
        File file = null;
        try {
            String content = call.getString("content", ""); byte[] bytes = content.getBytes(StandardCharsets.UTF_8);
            if (bytes.length == 0 || bytes.length > 2_000_000) throw new IllegalArgumentException();
            file = target(call, "csv");
            try (FileOutputStream output = new FileOutputStream(file)) { output.write(bytes); }
            saveReport(call, file, "text/csv", "csv");
        } catch (Exception failure) { if (file != null) file.delete(); call.reject("Could not save the CSV report. Try again."); }
    }
    @PluginMethod public void downloadXlsx(PluginCall call) {
        File file = null;
        try {
            String content = call.getString("content", "");
            if (content.length() > 8_000_000) throw new IllegalArgumentException();
            byte[] bytes = Base64.decode(content, Base64.DEFAULT);
            if (bytes.length < 22 || bytes[0] != 'P' || bytes[1] != 'K'
                    || bytes[2] != 3 || bytes[3] != 4) throw new IllegalArgumentException();
            file = target(call, "xlsx");
            try (FileOutputStream output = new FileOutputStream(file)) { output.write(bytes); }
            saveReport(call, file, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "xlsx");
        } catch (Exception failure) {
            if (file != null) file.delete();
            call.reject("Could not save the Excel report. Try again.");
        }
    }

    private String[] cells(org.json.JSONArray row, int width) throws Exception {
        if (row.length() != width) throw new IllegalArgumentException();
        String[] values = new String[width];
        for (int i = 0; i < width; i++) {
            Object value = row.get(i);
            if (!(value instanceof String) || ((String) value).length() > 2000) {
                throw new IllegalArgumentException();
            }
            values[i] = (String) value;
        }
        return values;
    }

    private List<String[]> grid(JSArray input, int width, int limit) throws Exception {
        if (input == null || input.length() > limit) throw new IllegalArgumentException();
        List<String[]> result = new ArrayList<>();
        int characters = 0;
        for (int i = 0; i < input.length(); i++) {
            String[] row = cells(input.getJSONArray(i), width);
            for (String value : row) characters += value.length();
            if (characters > 500_000) throw new IllegalArgumentException();
            result.add(row);
        }
        return result;
    }

    @PluginMethod public void downloadPdf(PluginCall call) {
        File file = null;
        try {
            String title = call.getString("title", "");
            String subtitle = call.getString("subtitle", "");
            boolean businessPlan = title.equals("Business plan");
            if (!(businessPlan || title.equals("Sales report") || title.equals("Product gross profit report"))
                    || subtitle.length() > 300) throw new IllegalArgumentException();
            JSArray headers = call.getArray("columns");
            if (businessPlan && (headers != null || subtitle.trim().isEmpty())) throw new IllegalArgumentException();
            String[] columns = null;
            String[] notes = null;
            List<String[]> summary = null;
            List<String[]> products = null;
            JSArray rows = call.getArray("rows");
            if (headers != null) {
                if (headers.length() != 3 && headers.length() != 6) throw new IllegalArgumentException();
                columns = cells(headers, headers.length());
                summary = grid(call.getArray("summary"), 2, 20);
                products = grid(call.getArray("products"), columns.length, 1500);
                JSArray suppliedNotes = call.getArray("notes");
                if (suppliedNotes == null || suppliedNotes.length() > 100) throw new IllegalArgumentException();
                notes = cells(suppliedNotes, suppliedNotes.length());
            } else {
                if (rows == null || rows.length() > 3000) throw new IllegalArgumentException();
                int characters = 0;
                for (int i = 0; i < rows.length(); i++) {
                    JSONObject row = rows.getJSONObject(i);
                    String kind = row.getString("kind"), value = row.getString("text");
                    if (!(kind.equals("heading") || kind.equals("text")) || value.length() > 2000) {
                        throw new IllegalArgumentException();
                    }
                    characters += value.length();
                    if (characters > 500_000) throw new IllegalArgumentException();
                }
            }
            file = target(call, "pdf");
            PdfDocument document = new PdfDocument();
            Painter painter = new Painter(document, title, subtitle);
            try {
                painter.start();
                if (columns != null) {
                    painter.structured(summary, columns, products, notes);
                } else {
                    for (int i = 0; i < rows.length(); i++) {
                        JSONObject row = rows.getJSONObject(i);
                        painter.row(row.getString("kind"), row.getString("text"));
                    }
                }
                painter.endPage();
                try (FileOutputStream output = new FileOutputStream(file)) { document.writeTo(output); }
            } finally {
                painter.endPage();
                if (painter.logo != null) painter.logo.recycle();
                document.close();
            }
            saveReport(call, file, "application/pdf", "pdf");
        } catch (Exception failure) { if (file != null) file.delete(); call.reject("Could not prepare or save the PDF. Please try again."); }
    }
    private class Painter {
        private static final int GREEN = 0xff145743;
        private static final int INK = 0xff183e33;
        private static final int MUTED = 0xff4e665d;
        private static final int TINT = 0xffedf5f0;
        private static final float LEFT = 36, RIGHT = 559, BOTTOM = 779;
        final PdfDocument document;
        final String title, subtitle;
        final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG);
        final Bitmap logo = BitmapFactory.decodeResource(getContext().getResources(), R.drawable.street_ceo_logo);
        PdfDocument.Page page;
        Canvas canvas;
        int number = 0;
        float y;

        Painter(PdfDocument document, String title, String subtitle) {
            this.document = document;
            this.title = title;
            this.subtitle = subtitle;
        }

        void textStyle(float size, int color, boolean bold) {
            paint.setTypeface(bold ? Typeface.DEFAULT_BOLD : Typeface.DEFAULT);
            paint.setTextSize(size);
            paint.setColor(color);
        }

        void fill(float left, float top, float right, float bottom, int color) {
            paint.setColor(color);
            canvas.drawRect(left, top, right, bottom, paint);
        }

        void start() {
            if (++number > 100) throw new IllegalArgumentException();
            page = document.startPage(new PdfDocument.PageInfo.Builder(595, 842, number).create());
            canvas = page.getCanvas();
            canvas.drawColor(Color.WHITE);
            fill(LEFT, 26, RIGHT, 101, GREEN);
            if (logo != null) {
                fill(46, 36, 101, 91, Color.WHITE);
                canvas.drawBitmap(logo, null, new RectF(49, 39, 98, 88), paint);
            }
            textStyle(9, 0xffc5e4d7, true);
            canvas.drawText(title.equals("Business plan") ? "STREET CEO  /  BUSINESS PLANNING" : "STREET CEO  /  SHOP REPORTS", 114, 45, paint);
            textStyle(20, Color.WHITE, true);
            canvas.drawText(title, 114, 68, paint);
            textStyle(9, MUTED, false);
            y = 117;
            for (String line : wrap(subtitle, RIGHT - LEFT)) {
                canvas.drawText(line, LEFT, y, paint);
                y += 13;
            }
            y += 10;
            fill(LEFT, 799, RIGHT, 800, 0xffd8e8df);
            textStyle(9, MUTED, false);
            canvas.drawText(title.equals("Business plan") ? "Street CEO  /  Business plan" : "Street CEO  /  Saved records", LEFT, 816, paint);
            String footer = "Page " + number;
            canvas.drawText(footer, RIGHT - paint.measureText(footer), 816, paint);
        }

        List<String> wrap(String value, float width) {
            List<String> lines = new ArrayList<>();
            String remaining = value.replaceAll("[\\p{Cntrl}]", " ").trim();
            while (!remaining.isEmpty()) {
                int end = Math.max(1, paint.breakText(remaining, true, width, null));
                if (end < remaining.length()) {
                    int space = remaining.lastIndexOf(' ', end);
                    if (space > end / 2) end = space;
                    if (end > 0 && Character.isHighSurrogate(remaining.charAt(end - 1))) end--;
                    if (end == 0) end = Character.charCount(remaining.codePointAt(0));
                }
                lines.add(remaining.substring(0, end));
                remaining = remaining.substring(end).trim();
            }
            if (lines.isEmpty()) lines.add("");
            return lines;
        }

        void endPage() {
            if (page != null) {
                document.finishPage(page);
                page = null;
            }
        }

        void ensure(float height) {
            if (y + height > BOTTOM) {
                endPage();
                start();
            }
        }

        void row(String kind, String value) {
            boolean heading = kind.equals("heading");
            textStyle(heading ? 13 : 10, heading ? GREEN : INK, heading);
            List<String> lines = wrap(value, RIGHT - LEFT);
            if (heading) {
                ensure(38);
                y += 5;
            }
            for (String line : lines) {
                ensure(15);
                textStyle(heading ? 13 : 10, heading ? GREEN : INK, heading);
                canvas.drawText(line, LEFT, y + 12, paint);
                y += 15;
            }
            y += heading ? 5 : 3;
        }

        void structured(List<String[]> summary, String[] columns, List<String[]> products, String[] notes) {
            row("heading", "Summary");
            for (int i = 0; i < summary.size(); i++) {
                tableRow(summary.get(i), new float[]{340, 183}, false, i, null);
            }
            y += 14;
            ensure(75);
            row("heading", "Product breakdown");
            float[] widths = columns.length == 3
                    ? new float[]{305, 80, 138} : new float[]{163, 52, 78, 76, 90, 64};
            tableRow(columns, widths, true, 0, null);
            if (products.isEmpty()) row("text", "No saved product sales in this period.");
            for (int i = 0; i < products.size(); i++) {
                tableRow(products.get(i), widths, false, i, columns);
            }
            y += 14;
            row("heading", "Notes");
            for (String note : notes) row("text", note);
        }

        void tableRow(String[] values, float[] widths, boolean header, int index, String[] repeatedHeader) {
            textStyle(header ? 9 : 10, INK, header);
            List<List<String>> wrapped = new ArrayList<>();
            int lines = 1;
            for (int i = 0; i < values.length; i++) {
                List<String> cell = wrap(values[i], widths[i] - 16);
                wrapped.add(cell);
                lines = Math.max(lines, cell.size());
            }
            // Draw only whole table rows on each page. Numeric cells remain right-aligned.
            float height = 12 * lines + 12;
            if (height > 540) throw new IllegalArgumentException("A report cell is too long");
            if (y + height > BOTTOM) {
                endPage();
                start();
                if (repeatedHeader != null) tableRow(repeatedHeader, widths, true, 0, null);
            }
            fill(LEFT, y, RIGHT, y + height, header ? GREEN : index % 2 == 0 ? TINT : Color.WHITE);
            fill(LEFT, y + height - 0.5f, RIGHT, y + height, 0xffd8e8df);
            textStyle(header ? 9 : 10, header ? Color.WHITE : INK, header);
            float x = LEFT;
            for (int i = 0; i < wrapped.size(); i++) {
                int lineIndex = 0;
                for (String line : wrapped.get(i)) {
                    float textX = i == 0 ? x + 8 : x + widths[i] - 8 - paint.measureText(line);
                    canvas.drawText(line, textX, y + 15 + 12 * lineIndex++, paint);
                }
                x += widths[i];
            }
            y += height;
        }
    }
}
