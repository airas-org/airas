import ReactMarkdown from "react-markdown";
import rehypeKatex from "rehype-katex";
import remarkMath from "remark-math";
import "katex/dist/katex.min.css";

interface MathMarkdownProps {
  children: string;
  className?: string;
}

/**
 * Markdown renderer with KaTeX math support.
 * Supports inline math ($...$) and block math ($$...$$).
 */
export function MathMarkdown({ children, className }: MathMarkdownProps) {
  return (
    <div className={className}>
      <ReactMarkdown remarkPlugins={[remarkMath]} rehypePlugins={[rehypeKatex]}>
        {children}
      </ReactMarkdown>
    </div>
  );
}
