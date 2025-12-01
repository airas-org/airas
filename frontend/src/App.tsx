// frontend/src/App.tsx
import { useState, useCallback } from "react"
import { SectionsSidebar } from "@/components/sections-sidebar"
import { MainContent } from "@/components/main-content"
import type { ResearchSection, WorkflowTree, WorkflowNode, FeatureType } from "@/types/research"

const mockSections: ResearchSection[] = [
  {
    id: "1",
    title: "Transformer Optimization Research",
    createdAt: new Date("2024-01-15"),
    status: "in-progress",
  },
  {
    id: "2",
    title: "GAN-based Image Generation",
    createdAt: new Date("2024-01-10"),
    status: "completed",
  },
  {
    id: "3",
    title: "Reinforcement Learning Study",
    createdAt: new Date("2024-01-05"),
    status: "completed",
  },
]

const initialWorkflowTree: WorkflowTree = {
  nodes: {},
  rootId: null,
  activeNodeId: null,
}

const featureOrder: FeatureType[] = [
  "papers",
  "method",
  "experiment-config",
  "code-generation",
  "experiment-run",
  "analysis",
  "paper-writing",
]

export default function App() {
  const [sections, setSections] = useState<ResearchSection[]>(mockSections)
  const [activeSection, setActiveSection] = useState<ResearchSection | null>(mockSections[0])
  const [activeFeature, setActiveFeature] = useState<string | null>(null)
  const [workflowTree, setWorkflowTree] = useState<WorkflowTree>(initialWorkflowTree)
  const [activeNodeId, setActiveNodeId] = useState<string | null>(null)

  const handleCreateSection = () => {
    const newSection: ResearchSection = {
      id: Date.now().toString(),
      title: "New Research Section",
      createdAt: new Date(),
      status: "in-progress",
    }
    setSections([newSection, ...sections])
    setActiveSection(newSection)
    setWorkflowTree(initialWorkflowTree)
    setActiveNodeId(null)
    setActiveFeature(null)
  }

  const getNodePathData = useCallback(
    (nodeId: string) => {
      const pathData: Record<FeatureType, WorkflowNode["data"]> =
        {} as Record<FeatureType, WorkflowNode["data"]>

      let currentId: string | null = nodeId
      while (currentId) {
        const node = workflowTree.nodes[currentId]
        if (node) {
          if (!pathData[node.type]) {
            pathData[node.type] = node.data || {}
          }
          currentId = node.parentId
        } else {
          break
        }
      }

      return pathData
    },
    [workflowTree],
  )

  const handleNavigate = useCallback(
    (nodeId: string) => {
      const node = workflowTree.nodes[nodeId]
      if (node) {
        setActiveNodeId(nodeId)
      }
    },
    [workflowTree],
  )

  const addWorkflowNode = useCallback(
    (
      type: FeatureType,
      parentNodeId: string | null,
      isBranch = false,
      data?: WorkflowNode["data"],
      snapshot?: WorkflowNode["snapshot"],
    ): string => {
      const newNodeId = `node-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`

      setWorkflowTree((prev) => {
        const newNodes = { ...prev.nodes }

        let branchIndex = 0
        if (parentNodeId) {
          const parentNode = prev.nodes[parentNodeId]
          if (parentNode) {
            if (isBranch) {
              const siblingBranches = parentNode.children.map((id) => prev.nodes[id]?.branchIndex || 0)
              const maxSiblingBranch =
                siblingBranches.length > 0 ? Math.max(...siblingBranches) : parentNode.branchIndex
              branchIndex = maxSiblingBranch + 1
            } else {
              branchIndex = parentNode.branchIndex
            }
          }
        } else if (isBranch) {
          let maxBranch = 0
          for (const nodeId in prev.nodes) {
            maxBranch = Math.max(maxBranch, prev.nodes[nodeId].branchIndex)
          }
          branchIndex = maxBranch + 1
        }

        const newNode: WorkflowNode = {
          id: newNodeId,
          type,
          branchIndex,
          parentId: parentNodeId,
          children: [],
          data: data || {},
          snapshot,
          createdAt: new Date(),
        }

        newNodes[newNodeId] = newNode

        if (parentNodeId && newNodes[parentNodeId]) {
          newNodes[parentNodeId] = {
            ...newNodes[parentNodeId],
            children: [...newNodes[parentNodeId].children, newNodeId],
          }
        }

        return {
          nodes: newNodes,
          rootId: prev.rootId || newNodeId,
          activeNodeId: newNodeId,
        }
      })

      setActiveNodeId(newNodeId)
      return newNodeId
    },
    [],
  )

  const createBranchFromNode = useCallback(
    (sourceNodeId: string, newType: FeatureType): string => {
      const sourceNode = workflowTree.nodes[sourceNodeId]
      if (!sourceNode || !sourceNode.parentId) {
        return addWorkflowNode(newType, sourceNodeId, false)
      }
      return addWorkflowNode(newType, sourceNode.parentId, true)
    },
    [workflowTree, addWorkflowNode],
  )

  const updateNodeData = useCallback((nodeId: string, data: Partial<WorkflowNode["data"]>) => {
    setWorkflowTree((prev) => ({
      ...prev,
      nodes: {
        ...prev.nodes,
        [nodeId]: {
          ...prev.nodes[nodeId],
          data: {
            ...prev.nodes[nodeId]?.data,
            ...data,
          },
        },
      },
    }))
  }, [])

  const updateNodeSnapshot = useCallback((nodeId: string, snapshot: WorkflowNode["snapshot"]) => {
    setWorkflowTree((prev) => ({
      ...prev,
      nodes: {
        ...prev.nodes,
        [nodeId]: {
          ...prev.nodes[nodeId],
          snapshot,
        },
      },
    }))
  }, [])

  const resetDownstreamSections = useCallback((_fromType: FeatureType) => {
    // ここはそのまま
  }, [])

  return (
    <div className="flex h-screen bg-background">
      <SectionsSidebar
        sections={sections}
        activeSection={activeSection}
        onSelectSection={setActiveSection}
        onCreateSection={handleCreateSection}
      />
      <MainContent
        section={activeSection}
        activeFeature={activeFeature}
        setActiveFeature={setActiveFeature}
        workflowTree={workflowTree}
        activeNodeId={activeNodeId}
        setActiveNodeId={setActiveNodeId}
        addWorkflowNode={addWorkflowNode}
        createBranchFromNode={createBranchFromNode}
        updateNodeData={updateNodeData}
        updateNodeSnapshot={updateNodeSnapshot}
        resetDownstreamSections={resetDownstreamSections}
        getNodePathData={getNodePathData}
        onNavigate={handleNavigate}
      />
    </div>
  )
}
