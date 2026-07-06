import html2canvas from "html2canvas";
import { jsPDF } from "jspdf";

/** Экспорт DOM-элемента в многостраничный PDF (A4). */
export async function exportElementToPdf(
  element: HTMLElement,
  filename: string
): Promise<void> {
  const canvas = await html2canvas(element, {
    scale: 1.5,
    useCORS: true,
    backgroundColor: "#ffffff",
    logging: false,
  });

  const pdf = new jsPDF({ orientation: "p", unit: "mm", format: "a4" });
  const pageWidth = pdf.internal.pageSize.getWidth();
  const pageHeight = pdf.internal.pageSize.getHeight();
  const margin = 10;
  const contentWidth = pageWidth - margin * 2;
  const contentHeight = pageHeight - margin * 2;

  const sliceHeightPx = Math.floor(
    (contentHeight / contentWidth) * canvas.width
  );
  let offsetY = 0;
  let page = 0;

  while (offsetY < canvas.height) {
    if (page > 0) pdf.addPage();

    const height = Math.min(sliceHeightPx, canvas.height - offsetY);
    const slice = document.createElement("canvas");
    slice.width = canvas.width;
    slice.height = height;
    const ctx = slice.getContext("2d");
    if (!ctx) throw new Error("Canvas 2D недоступен");

    ctx.fillStyle = "#ffffff";
    ctx.fillRect(0, 0, slice.width, slice.height);
    ctx.drawImage(
      canvas,
      0,
      offsetY,
      canvas.width,
      height,
      0,
      0,
      canvas.width,
      height
    );

    const imgData = slice.toDataURL("image/jpeg", 0.92);
    const sliceHeightMm = (height * contentWidth) / canvas.width;
    pdf.addImage(imgData, "JPEG", margin, margin, contentWidth, sliceHeightMm);

    offsetY += height;
    page += 1;
    if (page > 30) break;
  }

  pdf.save(sanitizeFilename(filename));
}

function sanitizeFilename(name: string): string {
  const trimmed = name.trim() || "plan.pdf";
  return trimmed.endsWith(".pdf") ? trimmed : `${trimmed}.pdf`;
}
