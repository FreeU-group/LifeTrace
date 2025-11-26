"use client";

import { useCallback, useMemo, useState } from "react";
import { diffLines, Change } from "diff";
import { Button } from "@/components/ui/button";
import { Check, X, ChevronDown, ChevronUp } from "lucide-react";
import { cn } from "@/lib/utils";

interface ChangeBlock {
  id: string;
  type: 'added' | 'removed' | 'modified' | 'unchanged';
  originalLines: string[];
  newLines: string[];
  lineNumber: number;
  accepted: boolean | null; // null = pending, true = accepted, false = rejected
}

interface InlineDiffViewerProps {
  original: string;
  suggested: string;
  onAccept: (mergedContent: string) => void;
  onCancel: () => void;
}

export function InlineDiffViewer({ original, suggested, onAccept, onCancel }: InlineDiffViewerProps) {
  const changeBlocks = useMemo(() => {
    const changes: Change[] = diffLines(original, suggested);
    const blocks: ChangeBlock[] = [];
    let lineNumber = 0;
    let blockId = 0;

    for (let i = 0; i < changes.length; i++) {
      const change = changes[i];
      const lines = change.value.split('\n').filter((line, idx, arr) => 
        idx < arr.length - 1 || line.length > 0
      );

      if (change.added || change.removed) {
        // Look for paired additions and removals (modifications)
        const nextChange = i + 1 < changes.length ? changes[i + 1] : null;
        
        if (change.removed && nextChange?.added) {
          // This is a modification
          blocks.push({
            id: `block-${blockId++}`,
            type: 'modified',
            originalLines: lines,
            newLines: nextChange.value.split('\n').filter((line, idx, arr) => 
              idx < arr.length - 1 || line.length > 0
            ),
            lineNumber,
            accepted: null,
          });
          i++; // Skip next change as we've processed it
          lineNumber += lines.length;
        } else if (change.added) {
          // Pure addition
          blocks.push({
            id: `block-${blockId++}`,
            type: 'added',
            originalLines: [],
            newLines: lines,
            lineNumber,
            accepted: null,
          });
        } else {
          // Pure removal
          blocks.push({
            id: `block-${blockId++}`,
            type: 'removed',
            originalLines: lines,
            newLines: [],
            lineNumber,
            accepted: null,
          });
          lineNumber += lines.length;
        }
      } else {
        // Unchanged lines
        blocks.push({
          id: `block-${blockId++}`,
          type: 'unchanged',
          originalLines: lines,
          newLines: lines,
          lineNumber,
          accepted: true, // Unchanged blocks are automatically accepted
        });
        lineNumber += lines.length;
      }
    }

    return blocks;
  }, [original, suggested]);

  const [blockStates, setBlockStates] = useState<Record<string, boolean | null>>(() => 
    Object.fromEntries(changeBlocks.map(block => [block.id, block.accepted]))
  );

  const [currentBlockIndex, setCurrentBlockIndex] = useState(0);

  const changeableBlocks = useMemo(() => 
    changeBlocks.filter(b => b.type !== 'unchanged'),
    [changeBlocks]
  );

  const navigateToBlock = useCallback((direction: 'next' | 'prev') => {
    const changeIndices = changeBlocks
      .map((block, idx) => block.type !== 'unchanged' ? idx : -1)
      .filter(idx => idx !== -1);

    if (changeIndices.length === 0) return;

    if (direction === 'next') {
      // Find next unhandled change (where state is null)
      const nextUnhandledIdx = changeIndices.find(idx => {
        const block = changeBlocks[idx];
        return idx > currentBlockIndex && blockStates[block.id] === null;
      });
      
      // If found, go to it; otherwise wrap to first unhandled
      if (nextUnhandledIdx !== undefined) {
        setCurrentBlockIndex(nextUnhandledIdx);
        document.getElementById(`change-block-${nextUnhandledIdx}`)?.scrollIntoView({ behavior: 'smooth', block: 'center' });
      } else {
        // Wrap to first unhandled change
        const firstUnhandledIdx = changeIndices.find(idx => {
          const block = changeBlocks[idx];
          return blockStates[block.id] === null;
        });
        if (firstUnhandledIdx !== undefined) {
          setCurrentBlockIndex(firstUnhandledIdx);
          document.getElementById(`change-block-${firstUnhandledIdx}`)?.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
      }
    } else {
      // Find previous unhandled change
      const prevUnhandledIndices = changeIndices.filter(idx => {
        const block = changeBlocks[idx];
        return idx < currentBlockIndex && blockStates[block.id] === null;
      });
      
      if (prevUnhandledIndices.length > 0) {
        const prevIdx = prevUnhandledIndices[prevUnhandledIndices.length - 1];
        setCurrentBlockIndex(prevIdx);
        document.getElementById(`change-block-${prevIdx}`)?.scrollIntoView({ behavior: 'smooth', block: 'center' });
      } else {
        // Wrap to last unhandled change
        const unhandledIndices = changeIndices.filter(idx => {
          const block = changeBlocks[idx];
          return blockStates[block.id] === null;
        });
        if (unhandledIndices.length > 0) {
          const lastIdx = unhandledIndices[unhandledIndices.length - 1];
          setCurrentBlockIndex(lastIdx);
          document.getElementById(`change-block-${lastIdx}`)?.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
      }
    }
  }, [changeBlocks, currentBlockIndex, blockStates]);

  const buildMergedContentFromStates = useCallback((states: Record<string, boolean | null>) => {
    const lines: string[] = [];
    
    changeBlocks.forEach(block => {
      const state = states[block.id];
      
      if (block.type === 'unchanged') {
        lines.push(...block.originalLines);
      } else if (block.type === 'added') {
        if (state === true) {
          lines.push(...block.newLines);
        }
        // If rejected, don't add anything
      } else if (block.type === 'removed') {
        if (state === false) {
          // Keep the original lines
          lines.push(...block.originalLines);
        }
        // If accepted, don't add anything (deletion is accepted)
      } else if (block.type === 'modified') {
        if (state === true) {
          // Accept modification - use new lines
          lines.push(...block.newLines);
        } else if (state === false) {
          // Reject modification - keep original lines
          lines.push(...block.originalLines);
        } else {
          // Pending - keep original for now
          lines.push(...block.originalLines);
        }
      }
    });

    return lines.join('\n');
  }, [changeBlocks]);

  const handleBlockAccept = useCallback((blockId: string) => {
    setBlockStates(prev => {
      const newStates = { ...prev, [blockId]: true };
      
      // Check if all changes are addressed
      const allAddressed = changeBlocks.every(block => {
        if (block.type === 'unchanged') return true;
        const state = newStates[block.id];
        return state !== null;
      });
      
      // If all addressed, apply changes immediately
      if (allAddressed) {
        setTimeout(() => {
          const merged = buildMergedContentFromStates(newStates);
          onAccept(merged);
        }, 150);
      } else {
        // Navigate to next unhandled change
        setTimeout(() => navigateToBlock('next'), 100);
      }
      
      return newStates;
    });
  }, [changeBlocks, onAccept, buildMergedContentFromStates, navigateToBlock]);

  const handleBlockReject = useCallback((blockId: string) => {
    setBlockStates(prev => {
      const newStates = { ...prev, [blockId]: false };
      
      // Check if all changes are addressed
      const allAddressed = changeBlocks.every(block => {
        if (block.type === 'unchanged') return true;
        const state = newStates[block.id];
        return state !== null;
      });
      
      // If all addressed, apply changes immediately
      if (allAddressed) {
        setTimeout(() => {
          const merged = buildMergedContentFromStates(newStates);
          onAccept(merged);
        }, 150);
      } else {
        // Navigate to next unhandled change
        setTimeout(() => navigateToBlock('next'), 100);
      }
      
      return newStates;
    });
  }, [changeBlocks, onAccept, buildMergedContentFromStates, navigateToBlock]);

  const handleAcceptAll = useCallback(() => {
    const newStates: Record<string, boolean | null> = {};
    changeBlocks.forEach(block => {
      newStates[block.id] = block.type === 'unchanged' ? true : true;
    });
    
    // Apply changes immediately
    setTimeout(() => {
      const merged = buildMergedContentFromStates(newStates);
      onAccept(merged);
    }, 150);
  }, [changeBlocks, onAccept, buildMergedContentFromStates]);

  const handleRejectAll = useCallback(() => {
    const newStates: Record<string, boolean | null> = {};
    changeBlocks.forEach(block => {
      newStates[block.id] = block.type === 'unchanged' ? true : false;
    });
    
    // Apply changes immediately
    setTimeout(() => {
      const merged = buildMergedContentFromStates(newStates);
      onAccept(merged);
    }, 150);
  }, [changeBlocks, onAccept, buildMergedContentFromStates]);

  const pendingCount = useMemo(() => 
    Object.values(blockStates).filter(state => state === null).length,
    [blockStates]
  );

  return (
    <div className="flex flex-col h-full">
      {/* Toolbar */}
      <div className="flex items-center justify-between gap-3 p-4 border-b bg-muted/30">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium">
            {changeableBlocks.length} change{changeableBlocks.length !== 1 ? 's' : ''}
          </span>
          {pendingCount > 0 && (
            <span className="text-xs text-muted-foreground">
              ({pendingCount} pending)
            </span>
          )}
        </div>
        
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => navigateToBlock('prev')}
            disabled={changeableBlocks.length === 0}
          >
            <ChevronUp className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => navigateToBlock('next')}
            disabled={changeableBlocks.length === 0}
          >
            <ChevronDown className="h-4 w-4" />
          </Button>
          
          <div className="w-px h-6 bg-border mx-1" />
          
          <Button
            variant="outline"
            size="sm"
            onClick={handleAcceptAll}
          >
            Accept All
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={handleRejectAll}
            className="gap-2"
          >
            <X className="h-4 w-4" />
            Reject All
          </Button>
          
          <div className="w-px h-6 bg-border mx-1" />
          
          <Button
            variant="ghost"
            size="sm"
            onClick={onCancel}
          >
            Cancel
          </Button>
        </div>
      </div>

      {/* Diff Content */}
      <div className="flex-1 overflow-y-auto p-4 bg-background">
        <div className="max-w-4xl mx-auto font-mono text-sm">
          {changeBlocks.map((block, idx) => {
            const state = blockStates[block.id];
            const isCurrentBlock = idx === currentBlockIndex;

            if (block.type === 'unchanged') {
              return (
                <div key={block.id} className="py-1">
                  {block.originalLines.map((line, lineIdx) => (
                    <div key={lineIdx} className="px-4 py-0.5 text-muted-foreground/60">
                      {line || ' '}
                    </div>
                  ))}
                </div>
              );
            }

            return (
              <div
                key={block.id}
                id={`change-block-${idx}`}
                className={cn(
                  "my-2 rounded-lg border-2 transition-all",
                  isCurrentBlock ? "border-primary" : "border-transparent",
                  state === true && "bg-green-50 dark:bg-green-950/20",
                  state === false && "bg-red-50 dark:bg-red-950/20",
                  state === null && "bg-blue-50 dark:bg-blue-950/20"
                )}
              >
                <div className="flex items-start gap-2 p-3">
                  <div className="flex-1">
                    {/* Removed/Modified original lines */}
                    {(block.type === 'removed' || block.type === 'modified') && block.originalLines.length > 0 && (
                      <div className={cn(
                        "mb-2",
                        state === true && "opacity-50 line-through"
                      )}>
                        {block.originalLines.map((line, lineIdx) => (
                          <div
                            key={`old-${lineIdx}`}
                            className="px-3 py-0.5 bg-red-100 dark:bg-red-900/30 text-red-900 dark:text-red-300 rounded"
                          >
                            <span className="text-red-600 dark:text-red-400 mr-2">-</span>
                            {line || ' '}
                          </div>
                        ))}
                      </div>
                    )}

                    {/* Added/Modified new lines */}
                    {(block.type === 'added' || block.type === 'modified') && block.newLines.length > 0 && (
                      <div className={cn(
                        state === false && "opacity-50 line-through"
                      )}>
                        {block.newLines.map((line, lineIdx) => (
                          <div
                            key={`new-${lineIdx}`}
                            className="px-3 py-0.5 bg-green-100 dark:bg-green-900/30 text-green-900 dark:text-green-300 rounded"
                          >
                            <span className="text-green-600 dark:text-green-400 mr-2">+</span>
                            {line || ' '}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Accept/Reject buttons */}
                  <div className="flex gap-1 shrink-0">
                    <Button
                      variant={state === true ? "default" : "ghost"}
                      size="sm"
                      onClick={() => handleBlockAccept(block.id)}
                      className="h-8 w-8 p-0"
                    >
                      <Check className="h-4 w-4" />
                    </Button>
                    <Button
                      variant={state === false ? "destructive" : "ghost"}
                      size="sm"
                      onClick={() => handleBlockReject(block.id)}
                      className="h-8 w-8 p-0"
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
