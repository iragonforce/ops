import os
import subprocess
from shutil import which


def find_soffice():
    # Prefer PATH
    p = which("soffice") or which("libreoffice")
    if p:
        return p
    # Common macOS locations
    candidates = [
        "/Applications/LibreOffice.app/Contents/MacOS/soffice",
        "/opt/homebrew/bin/soffice",
        "/usr/local/bin/soffice",
        "/usr/bin/soffice",
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return None


def find_ghostscript():
    return which("gs") or which("gswin64c") or which("gswin32c")


def compress_pdf(pdf_path):
    """Compress a PDF in place using Ghostscript's low-size PDF preset."""
    gs = find_ghostscript()
    if not gs:
        raise RuntimeError(
            "Ghostscript not found. Install it with 'brew install ghostscript'."
        )

    compressed_path = pdf_path + ".compressed.pdf"
    cmd = [
        gs,
        "-sDEVICE=pdfwrite",
        "-dCompatibilityLevel=1.4",
        # Lower-resolution output intended for screen use and smaller files.
        "-dPDFSETTINGS=/screen",
        "-dDetectDuplicateImages=true",
        "-dNOPAUSE",
        "-dBATCH",
        "-dQUIET",
        f"-sOutputFile={compressed_path}",
        pdf_path,
    ]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if proc.returncode != 0:
        if os.path.exists(compressed_path):
            os.remove(compressed_path)
        raise RuntimeError(
            f"Ghostscript failed for {os.path.basename(pdf_path)}.\n"
            f"STDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
        )

    original_size = os.path.getsize(pdf_path)
    compressed_size = os.path.getsize(compressed_path)
    os.replace(compressed_path, pdf_path)
    ratio = compressed_size / original_size if original_size else 0
    print(
        f"Compressed {os.path.basename(pdf_path)}: "
        f"{ratio:.0%} of original"
    )


def convert_pptx_to_pdf(input_folder, output_folder):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    soffice = find_soffice()
    if not soffice:
        raise RuntimeError(
            "LibreOffice (soffice) not found. Install LibreOffice and ensure 'soffice' is on PATH."
        )

    for filename in os.listdir(input_folder):
        if filename.lower().endswith((".pptx", ".ppt")):
            pptx_path = os.path.join(input_folder, filename)
            pdf_path = os.path.join(output_folder, os.path.splitext(filename)[0] + ".pdf")

            cmd = [
                soffice,
                "--headless",
                "--invisible",
                "--nocrashreport",
                "--nodefault",
                "--nolockcheck",
                "--nologo",
                "--convert-to", "pdf",
                "--outdir", output_folder,
                pptx_path,
            ]
            proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if proc.returncode != 0:
                raise RuntimeError(
                    f"LibreOffice failed for {filename}.\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
                )
            print(f"Converted {filename} to PDF -> {pdf_path}")
            compress_pdf(pdf_path)


# Paths for input and output
input_folder = os.path.dirname(os.path.abspath(__file__))  # Current folder
output_folder = os.path.join(input_folder, "converted_pdfs")

# Convert .pptx to .pdf
convert_pptx_to_pdf(input_folder, output_folder)
print(f"Converted PDFs are in: {output_folder}")
