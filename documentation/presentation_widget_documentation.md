# UNAI Rich Presentations Widget: Dropdowns, Glossary Tooltips & PDF Outline Exporter

This specification details the updated **Mini-Presentations Widget** for the UNAI educational agent (Professor Al), implementing:
1. **Interactive Expandable Dropdowns:** Keeping slides compact and digestible during screen lectures, but rendering them **fully expanded and styled** in the downloaded vector PDF notes.
2. **Glossary Tooltips:** Triggering custom absolute hover popups over key terms.
3. **Deduplicated Print Glossary Booklet:** Compiling a beautiful, alphabetical **"Glossary of Key Terms"** sheet at the end of the exported PDF.

---

## 1. Updated Schema & JSON Protocol Specification

When presenting rich slides, the backend calls the tool `create_presentation` with this updated JSON structure:

### Token Payload Format
```json
{
  "topic": "Types of Biological Sexes",
  "slides": [
    {
      "slide_number": 1,
      "title": "Understanding Biological Sex",
      "content": "Biological sex refers to the physical and physiological characteristics that define the differences between males, females, and intersex individuals.",
      "dropdowns": [
        {
          "header": "🔍 What are Chromosomes?",
          "body": "Chromosomes are long DNA molecules that carry part or all of the genetic material of an organism. In humans, sex chromosomes (XX or XY) determine biological sex."
        },
        {
          "header": "🧪 The Role of Hormones",
          "body": "Hormones like Testosterone and Estrogen act as chemical messengers, guiding gender development, physical growth, and cell differentiation."
        }
      ],
      "tooltips": [
        {
          "word": "Chromosomes",
          "definition": "Long DNA molecules that carry the genetic blueprints of cell structure and characteristics."
        },
        {
          "word": "Hormones",
          "definition": "Chemical messengers produced by glands that regulate body systems and cellular growth."
        }
      ]
    }
  ]
}
```

---

## 2. Updated Frontend React Widget Code

Give this exact source code to the frontend team to replace their existing `src/components/widgets/PresentationWidget.tsx` component:

```tsx
import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface DropdownItem {
  header: string;
  body: string;
}

interface TooltipItem {
  word: string;
  definition: string;
}

interface Slide {
  slide_number: number;
  title: string;
  content: string;
  dropdowns?: DropdownItem[];
  tooltips?: TooltipItem[];
}

interface PresentationWidgetProps {
  topic: string;
  slides: Slide[];
}

export function PresentationWidget({ topic, slides }: PresentationWidgetProps) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [direction, setDirection] = useState(1);

  if (!slides || slides.length === 0) return null;
  const currentSlide = slides[currentIndex];
  const totalSlides = slides.length;
  const completionPercentage = ((currentIndex + 1) / totalSlides) * 100;

  const handleNext = () => {
    if (currentIndex < totalSlides - 1) {
      setDirection(1);
      setCurrentIndex(prev => prev + 1);
    }
  };

  const handlePrev = () => {
    if (currentIndex > 0) {
      setDirection(-1);
      setCurrentIndex(prev => prev - 1);
    }
  };

  // Safe text parser that injects interactive hover CSS tooltips for glossary keywords
  const renderTextWithTooltips = (text: string, tooltips: TooltipItem[]) => {
    if (!tooltips || tooltips.length === 0) return text;

    // Sort tooltips by length descending to match longer keywords first and prevent partial word replacements
    const sortedTooltips = [...tooltips].sort((a, b) => b.word.length - a.word.length);
    
    // Construct single regex with word boundary matching
    const pattern = sortedTooltips.map(t => escapeRegExp(t.word)).join('|');
    const regex = new RegExp(`\\b(${pattern})\\b`, 'gi');

    const parts = text.split(regex);
    if (parts.length === 1) return text;

    return parts.map((part, index) => {
      const matchingTooltip = sortedTooltips.find(t => t.word.toLowerCase() === part.toLowerCase());
      if (matchingTooltip) {
        return (
          <span 
            key={index} 
            className="border-b border-dashed border-[var(--color-accent)] font-bold cursor-help relative group inline text-[var(--color-accent)]"
          >
            {part}
            {/* Absolute positioning CSS Hover Tooltip Card */}
            <span className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 w-64 bg-slate-950 dark:bg-slate-900 text-slate-100 text-[11px] rounded-xl p-3 shadow-xl opacity-0 pointer-events-none group-hover:opacity-100 group-hover:pointer-events-auto transition-all duration-200 z-50 text-left font-normal border border-slate-800 leading-relaxed block">
              <strong className="text-[var(--color-accent)] block mb-1 font-extrabold uppercase tracking-wider text-[9px]">Term Definition</strong>
              {matchingTooltip.definition}
              {/* Arrow */}
              <span className="absolute top-full left-1/2 transform -translate-x-1/2 -mt-1 border-4 border-transparent border-t-slate-950 dark:border-t-slate-900" />
            </span>
          </span>
        );
      }
      return part;
    });
  };

  const escapeRegExp = (string: string) => {
    return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  };

  // Browser-Native PDF Exporter (Automatically expands dropdowns & compiles Glossary Sheet)
  const handleExportPDF = () => {
    const printWindow = window.open('', '_blank', 'width=850,height=1100');
    if (!printWindow) {
      alert("Naku! Please allow popups in your browser to save slides as PDF.");
      return;
    }

    // 1. Compile each slide page (with dropdowns fully expanded!)
    const compiledSlidesHTML = slides.map(slide => {
      const slideTooltips = slide.tooltips || [];
      const dropdownsHTML = slide.dropdowns ? slide.dropdowns.map(drop => `
        <div class="print-dropdown">
          <div class="print-dropdown-header">${drop.header}</div>
          <div class="print-dropdown-body">${drop.body}</div>
        </div>
      `).join('') : '';

      return `
        <div class="slide-page">
          <div class="print-header">
            <div style="display: flex; align-items: center; gap: 8px;">
              <img src="${window.location.origin}/UNAI.svg" style="width: 22px; height: 22px; object-fit: contain;" />
              <div class="unai-pill" style="margin: 0;">UNAI Edu</div>
            </div>
            <div class="slide-num">Slide ${slide.slide_number} of ${totalSlides}</div>
          </div>
          <h2 class="slide-title">${slide.title || `Concept Focus`}</h2>
          <div class="slide-body">
            <div class="paragraph">${slide.content}</div>
            ${dropdownsHTML}
          </div>
          <div class="print-footer">Professor Al — teaching AI for Filipinos, by Filipinos &bull; UNAI Initiative</div>
        </div>
      `;
    }).join('');

    // 2. Compile deduplicated global Glossary booklet sheet
    const glossaryMap = new Map();
    slides.forEach(s => {
      if (s.tooltips) {
        s.tooltips.forEach(t => {
          const key = t.word.trim().toUpperCase();
          if (key && !glossaryMap.has(key)) {
            glossaryMap.set(key, { word: t.word.trim(), definition: t.definition });
          }
        });
      }
    });
    
    // Sort glossary terms alphabetically
    const glossaryList = Array.from(glossaryMap.values()).sort((a, b) => a.word.localeCompare(b.word));
    
    const glossaryHTML = glossaryList.length > 0 ? `
      <div class="slide-page">
        <div class="print-header">
          <div style="display: flex; align-items: center; gap: 8px;">
            <img src="${window.location.origin}/UNAI.svg" style="width: 22px; height: 22px; object-fit: contain;" />
            <div class="unai-pill" style="margin: 0;">UNAI Edu</div>
          </div>
          <div class="slide-num">Glossary</div>
        </div>
        <h2 class="slide-title">Glossary of Key Terms</h2>
        <div class="slide-body">
          <div class="glossary-grid">
            ${glossaryList.map(item => `
              <div class="glossary-item">
                <div class="glossary-word">${item.word}</div>
                <div class="glossary-definition">${item.definition}</div>
              </div>
            `).join('')}
          </div>
        </div>
        <div class="print-footer">Professor Al — teaching AI for Filipinos, by Filipinos &bull; UNAI Initiative</div>
      </div>
    ` : '';

    printWindow.document.write(`
      <html>
        <head>
          <title>${topic} — UNAI Presentation Booklet</title>
          <style>
            @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800;900&display=swap');
            @page {
              size: auto;
              margin: 0;
            }
            body {
              font-family: 'Outfit', sans-serif;
              color: #0f172a;
              background-color: #ffffff;
              margin: 0;
              padding: 0;
              -webkit-print-color-adjust: exact;
              print-color-adjust: exact;
            }
            .slide-page {
              page-break-after: always;
              padding: 80px;
              box-sizing: border-box;
              min-height: 100vh;
              display: flex;
              flex-direction: column;
              border-bottom: 2px dashed #cbd5e1;
              position: relative;
            }
            @media print {
              .slide-page {
                border-bottom: none;
                height: 100vh;
                min-height: 100vh;
                padding: 80px 100px;
              }
            }
            .print-header {
              display: flex;
              justify-content: space-between;
              align-items: center;
              border-bottom: 2px solid #ff6b00;
              padding-bottom: 12px;
              margin-bottom: 40px;
            }
            .unai-pill {
              background-color: #ff6b00;
              color: #ffffff;
              font-size: 11px;
              font-weight: 900;
              text-transform: uppercase;
              letter-spacing: 1px;
              padding: 4px 12px;
              border-radius: 9999px;
            }
            .slide-num {
              font-size: 12px;
              font-weight: 600;
              color: #64748b;
            }
            .slide-title {
              font-size: 28px;
              font-weight: 900;
              margin: 0 0 24px 0;
              color: #0f172a;
            }
            .slide-body {
              flex: 1;
              font-size: 16px;
              line-height: 1.6;
              color: #334155;
            }
            .paragraph {
              margin: 0 0 24px 0;
              white-space: pre-line;
            }
            .print-dropdown {
              border-left: 4px solid #ff6b00;
              background-color: #f8fafc;
              padding: 16px 20px;
              margin-bottom: 20px;
              border-radius: 0 12px 12px 0;
            }
            .print-dropdown-header {
              font-weight: 800;
              font-size: 14px;
              color: #1e293b;
              margin-bottom: 6px;
            }
            .print-dropdown-body {
              font-size: 13.5px;
              color: #475569;
              line-height: 1.5;
            }
            .glossary-grid {
              display: flex;
              flex-direction: column;
              gap: 20px;
              margin-top: 10px;
            }
            .glossary-item {
              padding-bottom: 16px;
              border-bottom: 1px solid #e2e8f0;
            }
            .glossary-word {
              font-weight: 900;
              font-size: 16px;
              color: #ff6b00;
              margin-bottom: 4px;
            }
            .glossary-definition {
              font-size: 14px;
              color: #475569;
              line-height: 1.5;
            }
            .print-footer {
              border-top: 1px solid #e2e8f0;
              padding-top: 12px;
              margin-top: 40px;
              font-size: 10px;
              font-weight: 600;
              text-transform: uppercase;
              letter-spacing: 0.5px;
              color: #94a3b8;
              text-align: center;
            }
          </style>
        </head>
        <body>
          <div class="slide-page" style="justify-content: center; align-items: center; text-align: center;">
            <img src="${window.location.origin}/UNAI.svg" style="width: 100px; height: 100px; object-fit: contain; margin-bottom: 24px;" />
            <div class="unai-pill" style="font-size: 16px; padding: 6px 20px;">UNAI EDU</div>
            <h1 style="font-size: 42px; font-weight: 900; color: #0f172a; margin: 24px 0 12px 0;">${topic}</h1>
            <p style="font-size: 16px; color: #64748b; margin: 0 0 40px 0;">Presentation Slides Booklet & Lecture Notes</p>
            <p style="font-size: 12px; color: #94a3b8; font-weight: 600; text-transform: uppercase; letter-spacing: 1px;">Prepared by Professor Al &bull; For Filipinos, By Filipinos</p>
          </div>
          ${compiledSlidesHTML}
          ${glossaryHTML}
          <script>
            window.onload = function() {
              window.print();
              setTimeout(function() { window.close(); }, 500);
            }
          </script>
        </body>
      </html>
    `);
    printWindow.document.close();
  };

  // Render Slide Content with lightweight markdown structure mapping
  const renderSlideContent = (content: string) => {
    const lines = content.split('\n');
    return lines.map((line, idx) => {
      const trimmed = line.trim();
      if (trimmed.startsWith('- ')) {
        return (
          <li key={idx} className="ml-4 list-disc text-sm sm:text-base text-slate-755 dark:text-slate-300 mb-2 leading-relaxed text-left font-normal">
            {renderTextWithTooltips(trimmed.substring(2), currentSlide.tooltips || [])}
          </li>
        );
      }
      if (trimmed === '') return <div key={idx} className="h-2" />;
      return (
        <p key={idx} className="text-sm sm:text-base text-slate-800 dark:text-slate-200 mb-3 leading-relaxed text-left font-normal">
          {renderTextWithTooltips(line, currentSlide.tooltips || [])}
        </p>
      );
    });
  };

  const isCliffhanger = currentSlide.content.trim().endsWith('?') || 
                        currentSlide.content.toLowerCase().includes('why?') || 
                        currentSlide.content.toLowerCase().includes('how?');
  
  let nextLabel = "Next Slide";
  if (currentIndex === totalSlides - 1) {
    nextLabel = "Finish Lesson";
  } else if (isCliffhanger) {
    nextLabel = "Discover Answer";
  }

  return (
    <div className="flex flex-col items-center bg-slate-50/50 dark:bg-black/10 p-6 sm:p-8 rounded-[36px] border border-neutral-200 dark:border-neutral-800 w-full mt-6 select-none shadow-md">
      
      {/* Header Panel */}
      <div className="w-full flex flex-col gap-3 mb-6 px-2 text-left">
        <div className="flex justify-between items-center">
          <div className="flex items-center gap-3">
            <h4 className="text-xs sm:text-sm font-extrabold uppercase tracking-wider text-[var(--color-accent)]">
              Interactive Slides: {topic}
            </h4>
            
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-white dark:bg-black/25 border border-neutral-200 dark:border-neutral-800 shadow-sm shrink-0 select-none">
              <img src="/UNAI.svg" alt="UNAI Logo" className="w-5 h-5 object-contain" />
              <span className="text-[10px] font-extrabold tracking-wider uppercase text-app-text">UNAI Edu</span>
            </div>
          </div>
          
          <div className="flex items-center gap-4">
            <button
              onClick={handleExportPDF}
              className="flex items-center gap-2 px-3 py-2 rounded-xl bg-white dark:bg-[#121212] hover:bg-slate-50 dark:hover:bg-white/5 border border-neutral-200 dark:border-neutral-800 text-[10px] sm:text-xs font-bold text-app-muted hover:text-[var(--color-accent)] transition-all shrink-0 shadow-sm outline-none"
              title="Download Presentation Slides Booklet as PDF"
            >
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2.5} stroke="currentColor" className="w-3.5 h-3.5 inline">
                <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
              </svg>
              <span>Download PDF</span>
            </button>
            <span className="text-xs font-bold text-app-muted">{currentIndex + 1} / {totalSlides}</span>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="w-full h-1.5 bg-neutral-200 dark:bg-neutral-800 rounded-full overflow-hidden">
          <motion.div
            className="h-full bg-[var(--color-accent)]"
            animate={{ width: `${completionPercentage}%` }}
            transition={{ type: "spring", stiffness: 200, damping: 25 }}
          />
        </div>
      </div>

      {/* Slide Content Card */}
      <div className="relative w-full overflow-hidden min-h-[300px] bg-white dark:bg-[#121212] border border-neutral-200 dark:border-neutral-800 rounded-[28px] shadow-sm flex flex-col">
        <AnimatePresence initial={false} mode="wait">
          <motion.div
            key={currentIndex}
            custom={direction}
            initial={{ opacity: 0, x: direction > 0 ? 80 : -80 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: direction > 0 ? -80 : 80 }}
            transition={{ type: "spring", stiffness: 300, damping: 26 }}
            className="p-8 sm:p-12 w-full h-full flex flex-col flex-1"
          >
            <span className="text-[10px] sm:text-xs text-app-muted uppercase font-bold tracking-wider mb-2 text-left block font-semibold">
              Slide {currentSlide.slide_number}: {currentSlide.title || 'Topic Focus'}
            </span>
            
            {/* Slide Body */}
            <div className="flex-1 mt-4">
              {renderSlideContent(currentSlide.content)}
              
              {/* Expandable Dropdowns Layout */}
              {currentSlide.dropdowns && currentSlide.dropdowns.length > 0 && (
                <div className="mt-6 space-y-3">
                  {currentSlide.dropdowns.map((drop, dropIdx) => (
                    <SlideDropdown 
                      key={dropIdx} 
                      header={drop.header} 
                      body={drop.body} 
                      tooltips={currentSlide.tooltips || []} 
                      renderTextWithTooltips={renderTextWithTooltips}
                    />
                  ))}
                </div>
              )}
            </div>
          </motion.div>
        </AnimatePresence>
      </div>

      {/* Slide Navigation Controls */}
      <div className="flex items-center gap-4 mt-6">
        <button
          type="button"
          disabled={currentIndex === 0}
          onClick={handlePrev}
          className="px-5 py-2.5 rounded-xl bg-white dark:bg-[#121212] border border-neutral-200 dark:border-neutral-800 text-xs sm:text-sm font-bold text-app-text disabled:opacity-40 select-none hover:bg-slate-50 dark:hover:bg-white/5 active:scale-[0.98] transition-all flex items-center gap-2"
        >
          Back
        </button>
        <button
          type="button"
          onClick={currentIndex === totalSlides - 1 ? undefined : handleNext}
          className="px-6 py-2.5 rounded-xl bg-[var(--color-accent)] hover:bg-[var(--color-accent-hover)] text-white font-extrabold text-xs sm:text-sm uppercase active:scale-[0.98] transition-all flex items-center gap-2 shadow-md"
        >
          {nextLabel}
        </button>
      </div>
    </div>
  );
}

// Collapsible Dropdown Component
interface SlideDropdownProps {
  header: string;
  body: string;
  tooltips: TooltipItem[];
  renderTextWithTooltips: (text: string, tooltips: TooltipItem[]) => React.ReactNode;
}

function SlideDropdown({ header, body, tooltips, renderTextWithTooltips }: SlideDropdownProps) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="border border-neutral-200 dark:border-neutral-800 rounded-2xl bg-slate-50 dark:bg-black/10 overflow-hidden text-left">
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between px-5 py-3.5 hover:bg-slate-100/50 dark:hover:bg-white/5 transition-colors text-left outline-none font-extrabold text-xs sm:text-sm text-slate-700 dark:text-slate-300 select-none"
      >
        <span>{header}</span>
        <svg
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          strokeWidth={2.5}
          stroke="currentColor"
          className={`w-3.5 h-3.5 text-slate-450 transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`}
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="m19.5 8.25-7.5 7.5-7.5-7.5" />
        </svg>
      </button>

      <AnimatePresence initial={false}>
        {isOpen && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2, ease: "easeOut" }}
            className="overflow-hidden"
          >
            <div className="px-5 pb-5 pt-2 border-t border-neutral-200/50 dark:border-neutral-800/50 bg-white dark:bg-[#121212] text-xs sm:text-sm text-slate-600 dark:text-slate-400 leading-relaxed font-normal">
              {renderTextWithTooltips(body, tooltips)}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
```
