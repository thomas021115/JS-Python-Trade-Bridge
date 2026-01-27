const MARKDOWN_MIME = "text/markdown;charset=utf-8";

export function downloadMarkdown(filename: string, content: string){
    const blob = new Blob([content], { type: MARKDOWN_MIME});
    const url = URL.createObjectURL(blob);

    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    link.click();

    URL.revokeObjectURL(url);
}

export function buildReportFilename(code: string){
    const d = new Date();
    const yyyy = d.getFullYear();
    const mm = String(d.getMonth() + 1).padStart(2, "0");
    const dd = String(d.getDate() + 1).padStart(2, "0");
    const hh = String(d.getHours()).padStart(2, "0");
    const min = String(d.getMinutes()).padStart(2, "0");
    return `ai-report_${code}_${yyyy}${mm}${dd}_${hh}${min}.md`;
}