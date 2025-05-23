import React, { memo, useMemo } from "react";
import { FilenameInput } from "./FilenameInput";
import { GenerateButton } from "./GenerateButton";
import { PDFGenerationRequest } from "../lib/api";
import { useTypography, useLayout, useFilename } from "./FormattingContext";

interface PDFActionsProps {
  markup: string;
}

function PDFActionsComponent({ markup }: PDFActionsProps) {
  // Get values from specific contexts to prevent unnecessary re-renders
  const { fontFamily, sizeLevel } = useTypography();
  const { spacing, autoWidthTables } = useLayout();
  const { filename } = useFilename();

  // Memoize the PDF request object to prevent unnecessary re-creation
  const pdfRequest: PDFGenerationRequest = useMemo(
    () => ({
      markup,
      font_family: fontFamily,
      size_level: sizeLevel,
      spacing,
      auto_width_tables: autoWidthTables,
      filename,
    }),
    [markup, fontFamily, sizeLevel, spacing, autoWidthTables, filename]
  );

  return (
    <div className="bg-white dark:bg-neutral-900 rounded-md shadow p-4 mb-4 min-w-64 border dark:border-neutral-800 ">
      <div className="flex items-end space-x-4">
        <FilenameInput />
      </div>
      <div className="flex justify-end items-end space-x-4 pt-4">
        <GenerateButton request={pdfRequest} disabled={!markup.trim()} />
      </div>
    </div>
  );
}

// Memoize the component to prevent unnecessary re-renders
export const PDFActions = memo(PDFActionsComponent);
