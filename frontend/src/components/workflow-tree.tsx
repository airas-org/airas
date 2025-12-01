"use client"

import type React from "react"

import { Search, Lightbulb, Settings2, Code2, Play, BarChart3, FileText } from "lucide-react"
import { cn } from "@/lib/utils"
import type { WorkflowTree as WorkflowTreeType, FeatureType } from "@/types/research"

const featureIcons: Record<FeatureType, React.ComponentType<{ className?: string }>> = {
  papers: Search,
  method: Lightbulb,
  "experiment-config": Settings2,
  "code-generation": Code2,
  "experiment-run": Play,
  analysis: BarChart3,
  "paper-writing": FileText,
}

const featureLabels: Record<FeatureType, string> = {
  papers: "論文取得",
  method: "新規手法",
  "experiment-config": "実験設定",
  "code-generation": "コード生成",
  "experiment-run": "実験実行",
  analysis: "結果分析",
  "paper-writing": "論文作成",
}

interface WorkflowTreeProps {
  workflowTree: WorkflowTreeType
  activeNodeId: string | null
  onNavigate: (nodeId: string) => void
}

// Helper to get all nodes at each level grouped by branch
function getTreeStructure(tree: WorkflowTreeType): { nodeId: string; branchIndex: number; level: number }[][] {
  if (!tree.rootId) return []

  const levels: { nodeId: string; branchIndex: number; level: number }[][] = []

  function traverse(nodeId: string, level: number) {
    const node = tree.nodes[nodeId]
    if (!node) return

    if (!levels[level]) levels[level] = []
    levels[level].push({ nodeId, branchIndex: node.branchIndex, level })

    // Sort children by branchIndex and traverse
    const sortedChildren = [...node.children].sort((a, b) => {
      const nodeA = tree.nodes[a]
      const nodeB = tree.nodes[b]
      return (nodeA?.branchIndex || 0) - (nodeB?.branchIndex || 0)
    })

    for (const childId of sortedChildren) {
      traverse(childId, level + 1)
    }
  }

  traverse(tree.rootId, 0)
  return levels
}

// Get max branch index in the tree
function getMaxBranchIndex(tree: WorkflowTreeType): number {
  let max = 0
  for (const nodeId in tree.nodes) {
    max = Math.max(max, tree.nodes[nodeId].branchIndex)
  }
  return max
}

export function WorkflowTree({ workflowTree, activeNodeId, onNavigate }: WorkflowTreeProps) {
  const levels = getTreeStructure(workflowTree)
  const maxBranch = getMaxBranchIndex(workflowTree)
  const columnCount = maxBranch + 1

  // Build a grid representation
  const grid: (string | null)[][] = []

  for (let levelIdx = 0; levelIdx < levels.length; levelIdx++) {
    const row: (string | null)[] = Array(columnCount).fill(null)
    for (const item of levels[levelIdx]) {
      row[item.branchIndex] = item.nodeId
    }
    grid.push(row)
  }

  if (grid.length === 0) {
    return (
      <div className="py-4 px-6 border-b border-border bg-muted/70">
        <div className="text-center text-muted-foreground text-sm">
          <p>まだ実行されたステップがありません</p>
          <p className="mt-1 text-xs">論文取得から始めてください</p>
        </div>
      </div>
    )
  }

  // A node is a branch point if it has multiple children
  const getBranchPointForNode = (nodeId: string): string | null => {
    const node = workflowTree.nodes[nodeId]
    if (!node || !node.parentId) return null

    const parent = workflowTree.nodes[node.parentId]
    if (!parent) return null

    // If parent has more than one child, this is a branched node
    if (parent.children.length > 1) {
      return node.parentId
    }
    return null
  }

  const isBranchedNode = (nodeId: string): boolean => {
    const node = workflowTree.nodes[nodeId]
    if (!node) return false
    return node.branchIndex > 0
  }

  const findNodeRowIndex = (searchNodeId: string): number => {
    for (let rowIdx = 0; rowIdx < grid.length; rowIdx++) {
      if (grid[rowIdx].includes(searchNodeId)) {
        return rowIdx
      }
    }
    return -1
  }

  const isCompletedNode = (nodeId: string): boolean => {
    if (activeNodeId === nodeId) return false
    const node = workflowTree.nodes[nodeId]
    if (!node) return false
    // Node is completed if it has snapshot data
    return node.snapshot !== undefined
  }

  return (
    <div className="py-4 px-6 border-b border-border bg-muted/70 overflow-x-auto">
      <div className="relative flex flex-col items-start">
        {grid.map((row, rowIdx) => (
          <div key={rowIdx} className="flex flex-col">
            <div className="flex flex-row gap-3">
              {row.map((nodeId, colIdx) => {
                if (!nodeId) {
                  return <div key={colIdx} className="w-32" />
                }

                const node = workflowTree.nodes[nodeId]
                const Icon = featureIcons[node.type]
                const isActive = activeNodeId === nodeId
                const isCompleted = isCompletedNode(nodeId)
                const label = featureLabels[node.type]

                // and connect to the branch point (leftward)
                const branchPointId = getBranchPointForNode(nodeId)
                const showLeftConnector = isBranchedNode(nodeId) && branchPointId !== null

                // Connect to the column where the branch point's main branch is
                let connectToCol = 0
                if (showLeftConnector && branchPointId) {
                  const branchPointRowIdx = findNodeRowIndex(branchPointId)
                  if (branchPointRowIdx >= 0) {
                    // Find the column of the branch point
                    for (let c = 0; c < grid[branchPointRowIdx].length; c++) {
                      if (grid[branchPointRowIdx][c] === branchPointId) {
                        connectToCol = c
                        break
                      }
                    }
                  }
                }

                const connectorWidth = showLeftConnector ? (colIdx - connectToCol) * (128 + 12) - 64 : 0

                return (
                  <div key={colIdx} className="relative flex items-center">
                    {showLeftConnector && (
                      <div className="absolute right-full top-1/2 h-0.5 bg-border -translate-y-1/2 w-6" />
                    )}

                    <button
                      onClick={() => onNavigate(nodeId)}
                      className={cn(
                        "w-32 flex flex-row items-center gap-2 px-2.5 py-2 rounded-lg border transition-all duration-200 bg-background",
                        isActive
                          ? "border-primary bg-primary text-primary-foreground shadow-lg shadow-primary/20"
                          : "border-border text-muted-foreground hover:border-muted-foreground hover:bg-muted/50",
                      )}
                    >
                      <div
                        className={cn(
                          "w-6 h-6 rounded-md flex items-center justify-center flex-shrink-0",
                          isActive ? "bg-white/20" : "bg-muted",
                        )}
                      >
                        <Icon
                          className={cn("w-3 h-3", isActive ? "text-primary-foreground" : "text-muted-foreground")}
                        />
                      </div>
                      <span className="text-xs font-medium text-left leading-tight">{label}</span>
                    </button>
                  </div>
                )
              })}
            </div>

            {/* Vertical connectors */}
            {rowIdx < grid.length - 1 && (
              <div className="flex flex-row gap-3 h-3">
                {row.map((nodeId, colIdx) => {
                  // Check if there's a node below in this column
                  const hasNodeBelow = grid[rowIdx + 1] && grid[rowIdx + 1][colIdx] !== null

                  // If so, don't show vertical connector from above
                  let nodeBelowIsBranched = false
                  if (hasNodeBelow && grid[rowIdx + 1][colIdx]) {
                    const belowNodeId = grid[rowIdx + 1][colIdx]!
                    const belowNode = workflowTree.nodes[belowNodeId]
                    if (belowNode && isBranchedNode(belowNodeId)) {
                      // Check if the parent is not in the same column
                      const parentId = belowNode.parentId
                      if (parentId) {
                        const parentRowIdx = findNodeRowIndex(parentId)
                        if (parentRowIdx >= 0) {
                          const parentCol = grid[parentRowIdx].indexOf(parentId)
                          if (parentCol !== colIdx) {
                            nodeBelowIsBranched = true
                          }
                        }
                      }
                    }
                  }

                  if (!nodeId && !hasNodeBelow) {
                    return <div key={colIdx} className="w-32" />
                  }

                  const showVerticalConnector = nodeId && hasNodeBelow && !nodeBelowIsBranched

                  return (
                    <div key={colIdx} className="w-32 flex justify-center">
                      {showVerticalConnector && (
                        <div className="relative h-full flex flex-col items-center">
                          <div className="w-0.5 h-full bg-border" />
                          <div className="w-1.5 h-1.5 rounded-full border-2 border-border bg-background" />
                        </div>
                      )}
                      {!showVerticalConnector && <div className="w-32" />}
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
