import csv
import importlib
import json
from pathlib import Path


class ExportService:
    _extensions = {
        "csv": ".csv",
        "xlsx": ".xlsx",
        "json": ".json",
        "npy": ".npy",
        "mat": ".mat",
        "txt": ".txt",
    }

    def export(self, filename, file_format, graphs, graph_ids, delimiter=","):
        rows = self._rows(graphs, graph_ids)
        writer = getattr(self, f"_write_{file_format}")
        writer(filename, rows, len(graph_ids) > 1, delimiter)

    def _rows(self, graphs, graph_ids):
        rows = []
        for graph_id in graph_ids:
            graph = graphs.get(graph_id)
            for point in graph.points:
                rows.append((graph.name, point.value_x, point.value_y))
        return rows

    def _filename(self, filename, file_format):
        path = Path(filename)
        if path.suffix.lower() != self._extensions[file_format]:
            path = path.with_suffix(self._extensions[file_format])
        return path

    def _write_csv(self, filename, rows, export_all, _delimiter):
        self._write_delimited(filename, rows, export_all, ",", "csv")

    def _write_txt(self, filename, rows, export_all, delimiter):
        self._write_delimited(filename, rows, export_all, delimiter, "txt")

    def _write_delimited(self, filename, rows, export_all, delimiter, file_format):
        with self._filename(filename, file_format).open(
            "w", newline="", encoding="utf-8"
        ) as file:
            writer = csv.writer(file, delimiter=delimiter)
            writer.writerow(["graph", "x", "y"] if export_all else ["x", "y"])
            if export_all:
                writer.writerows(rows)
            else:
                writer.writerows((value_x, value_y) for _, value_x, value_y in rows)

    def _write_json(self, filename, rows, export_all, _delimiter):
        data = [
            ({"graph": name, "x": value_x, "y": value_y} if export_all
             else {"x": value_x, "y": value_y})
            for name, value_x, value_y in rows
        ]
        with self._filename(filename, "json").open("w", encoding="utf-8") as file:
            json.dump(data, file, indent=2)

    def _write_xlsx(self, filename, rows, export_all, _delimiter):
        try:
            workbook_module = importlib.import_module("openpyxl")
        except ImportError as error:
            raise ImportError("XLSX export requires the openpyxl package.") from error

        workbook = workbook_module.Workbook()
        sheet = workbook.active
        sheet.append(["graph", "x", "y"] if export_all else ["x", "y"])
        for name, value_x, value_y in rows:
            sheet.append([name, value_x, value_y] if export_all else [value_x, value_y])
        workbook.save(self._filename(filename, "xlsx"))

    def _write_npy(self, filename, rows, export_all, _delimiter):
        try:
            numpy = importlib.import_module("numpy")
        except ImportError as error:
            raise ImportError("Numpy export requires the numpy package.") from error

        if export_all:
            data = numpy.array(rows, dtype=object)
        else:
            data = numpy.array([(x, y) for _, x, y in rows], dtype=float)
        numpy.save(self._filename(filename, "npy"), data, allow_pickle=True)

    def _write_mat(self, filename, rows, export_all, _delimiter):
        try:
            numpy = importlib.import_module("numpy")
            scipy_io = importlib.import_module("scipy.io")
        except ImportError as error:
            raise ImportError(
                "MATLAB export requires the numpy and scipy packages."
            ) from error

        data = {
            "x": numpy.array([x for _, x, _ in rows]),
            "y": numpy.array([y for _, _, y in rows]),
        }
        if export_all:
            data["graph"] = numpy.array([name for name, _, _ in rows], dtype=object)
        scipy_io.savemat(self._filename(filename, "mat"), data)
