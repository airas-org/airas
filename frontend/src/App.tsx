// frontend/src/App.tsx

import axios from "axios";
import { FileText, Github, UserCircle, X as XIcon } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { MainContent, type NavKey } from "@/components/main-content";
import { useAutonomousResearchSessions } from "@/components/pages/autonomous-research/use-autonomous-research-sessions";
import { SectionsSidebar } from "@/components/sections-sidebar";
import { isEnterpriseEnabled } from "@/ee/config";
import { cn } from "@/lib/utils";
import type { FeatureType, ResearchSection, WorkflowNode, WorkflowTree } from "@/types/research";

const mockResearchSections: ResearchSection[] = [
  {
    id: "1",
    title: "Untitled Research",
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
];

const initialWorkflowTree: WorkflowTree = {
  nodes: {},
  rootId: null,
  activeNodeId: null,
};

// Lazy-loaded EE components (only imported when EE is enabled)
type AuthGuardType = typeof import("@/ee/auth/components/AuthGuard").AuthGuard;
type UserMenuType = typeof import("@/ee/auth/components/UserMenu").UserMenu;
type AuthCallbackType = typeof import("@/ee/auth/components/AuthCallback").AuthCallback;

interface EEComponents {
  AuthGuard: AuthGuardType;
  UserMenu: UserMenuType;
  AuthCallback: AuthCallbackType;
}

function useEEComponents() {
  const [eeComponents, setEeComponents] = useState<EEComponents | null>(null);
  const [signInWithGoogle, setSignInWithGoogle] = useState<(() => Promise<void>) | null>(null);

  useEffect(() => {
    if (!isEnterpriseEnabled()) return;

    Promise.all([
      import("@/ee/auth/components/AuthGuard"),
      import("@/ee/auth/components/UserMenu"),
      import("@/ee/auth/components/AuthCallback"),
      import("@/ee/auth/lib/axios-interceptor"),
    ]).then(([authGuard, userMenu, authCallback, interceptor]) => {
      setEeComponents({
        AuthGuard: authGuard.AuthGuard,
        UserMenu: userMenu.UserMenu,
        AuthCallback: authCallback.AuthCallback,
      });
      axios.interceptors.request.use(interceptor.authRequestInterceptor);
      import("@/ee/auth/lib/supabase").then((mod) => {
        const signIn = async () => {
          const { error } = await mod.supabase.auth.signInWithOAuth({
            provider: "google",
            options: { redirectTo: `${window.location.origin}/auth/callback` },
          });
          if (error) throw error;
        };
        setSignInWithGoogle(() => signIn);
      });
    });
  }, []);

  return { eeComponents, signInWithGoogle };
}

export default function App() {
  const { eeComponents, signInWithGoogle } = useEEComponents();

  const [researchSections, setResearchSections] = useState<ResearchSection[]>(mockResearchSections);
  const [autoSections, setAutoSections] = useState<ResearchSection[]>([]);
  const [activeResearchSection, setActiveResearchSection] = useState<ResearchSection | null>(
    mockResearchSections[0],
  );
  const [activeAutoSection, setActiveAutoSection] = useState<ResearchSection | null>(null);
  const [activeFeature, setActiveFeature] = useState<string | null>(null);
  const [workflowTree, setWorkflowTree] = useState<WorkflowTree>(initialWorkflowTree);
  const [activeNodeId, setActiveNodeId] = useState<string | null>(null);
  // 現在、何が選ばれているか
  const [activeNav, setActiveNav] = useState<NavKey>("autonomous-research");
  const [sessionsExpanded, setSessionsExpanded] = useState(false);

  const { fetchAutoSections } = useAutonomousResearchSessions({
    setAutoSections,
    setActiveAutoSection,
  });

  const handleCreateSection = () => {
    const newSection: ResearchSection = {
      id: Date.now().toString(),
      title: "Untitled Research",
      createdAt: new Date(),
      status: "in-progress",
    };
    if (activeNav === "autonomous-research") {
      setActiveAutoSection(null);
    } else {
      setResearchSections([newSection, ...researchSections]);
      setActiveResearchSection(newSection);
    }
    setWorkflowTree(initialWorkflowTree);
    setActiveNodeId(null);
    setActiveFeature(null);
  };

  const handleToggleSessions = useCallback(() => {
    setSessionsExpanded((prev) => !prev);
  }, []);

  const handleNavigate = useCallback(
    (nodeId: string) => {
      const node = workflowTree.nodes[nodeId];
      if (node) {
        setActiveNodeId(nodeId);
        setActiveFeature(node.type);
      }
    },
    [workflowTree],
  );

  const addWorkflowNode = useCallback(
    (
      type: FeatureType,
      parentNodeId: string | null,
      isBranch = false,
      data?: WorkflowNode["data"],
      snapshot?: WorkflowNode["snapshot"],
    ): string => {
      const newNodeId = `node-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

      setWorkflowTree((prev) => {
        const newNodes = { ...prev.nodes };

        let branchIndex = 0;
        if (parentNodeId) {
          const parentNode = prev.nodes[parentNodeId];
          if (parentNode) {
            if (isBranch) {
              const siblingBranches = parentNode.children.map(
                (id) => prev.nodes[id]?.branchIndex || 0,
              );
              const maxSiblingBranch =
                siblingBranches.length > 0 ? Math.max(...siblingBranches) : parentNode.branchIndex;
              branchIndex = maxSiblingBranch + 1;
            } else {
              branchIndex = parentNode.branchIndex;
            }
          }
        } else if (isBranch) {
          let maxBranch = 0;
          for (const nodeId in prev.nodes) {
            maxBranch = Math.max(maxBranch, prev.nodes[nodeId].branchIndex);
          }
          branchIndex = maxBranch + 1;
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
        };

        newNodes[newNodeId] = newNode;

        if (parentNodeId && newNodes[parentNodeId]) {
          newNodes[parentNodeId] = {
            ...newNodes[parentNodeId],
            children: [...newNodes[parentNodeId].children, newNodeId],
          };
        }

        return {
          nodes: newNodes,
          rootId: prev.rootId || newNodeId,
          activeNodeId: newNodeId,
        };
      });

      setActiveNodeId(newNodeId);
      return newNodeId;
    },
    [],
  );

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
    }));
  }, []);

  const resetDownstreamSessions = useCallback((_fromType: FeatureType) => {
    // ここはそのまま
  }, []);

  const handleUpdateSectionTitle = useCallback(
    (title: string) => {
      if (activeNav === "autonomous-research") {
        if (!activeAutoSection) return;
        setAutoSections((prev) =>
          prev.map((s) => (s.id === activeAutoSection.id ? { ...s, title } : s)),
        );
        setActiveAutoSection((prev) => (prev ? { ...prev, title } : prev));
      } else {
        if (!activeResearchSection) return;
        setResearchSections((prev) =>
          prev.map((s) => (s.id === activeResearchSection.id ? { ...s, title } : s)),
        );
        setActiveResearchSection((prev) => (prev ? { ...prev, title } : prev));
      }
    },
    [activeAutoSection, activeNav, activeResearchSection],
  );

  const navItems: { key: NavKey; label: string; disabled?: boolean }[] = [
    { key: "papers", label: "Paper", disabled: true },
    { key: "assisted-research", label: "Assisted Research", disabled: true },
    { key: "autonomous-research", label: "Autonomous Research" },
  ];

  const handleNavChange = useCallback((key: NavKey) => {
    setActiveNav(key);
    if (key === "assisted-research") {
      setWorkflowTree(initialWorkflowTree);
      setActiveNodeId(null);
    }
  }, []);

  // Handle OAuth callback route
  if (isEnterpriseEnabled() && window.location.pathname === "/auth/callback") {
    if (!eeComponents) {
      return (
        <div className="flex min-h-screen items-center justify-center">
          <div className="text-muted-foreground">Loading...</div>
        </div>
      );
    }
    return <eeComponents.AuthCallback />;
  }

  const appContent = (
    <div className="flex min-h-screen flex-col bg-background">
      <header className="h-12 border-b border-border bg-card px-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <img src="/airas_logo.png" alt="AIRAS logo" className="h-8 w-auto" />
          <p className="text-base font-semibold text-foreground leading-none">AIRAS</p>
        </div>
        <div className="flex items-center gap-4">
          <a
            href="https://github.com/airas-org/airas"
            target="_blank"
            rel="noreferrer"
            className="text-muted-foreground hover:text-foreground transition-colors"
            aria-label="GitHub"
          >
            <Github className="h-6 w-6" />
          </a>
          <a
            href="https://airas-org.github.io/airas/"
            target="_blank"
            rel="noreferrer"
            className="text-muted-foreground hover:text-foreground transition-colors"
            aria-label="Documentation"
          >
            <FileText className="h-6 w-6" />
          </a>
          <a
            href="https://x.com/fuyu_quant"
            target="_blank"
            rel="noreferrer"
            className="text-muted-foreground hover:text-foreground transition-colors"
            aria-label="X (formerly Twitter)"
          >
            <XIcon className="h-6 w-6" />
          </a>
          {eeComponents ? (
            <eeComponents.UserMenu />
          ) : (
            <button
              type="button"
              className="flex items-center gap-2 rounded-md border border-border px-3 py-1.5 text-sm text-foreground hover:bg-muted/60 transition-colors"
              onClick={signInWithGoogle ?? undefined}
            >
              <UserCircle className="h-5 w-5" />
              <span>Login</span>
            </button>
          )}
        </div>
      </header>

      <div className="flex flex-1">
        <aside className="w-40 border-r border-border bg-card/60 flex-shrink-0 flex flex-col">
          <div className="flex flex-col gap-2 p-3">
            {navItems.map((item) => {
              const isActive = activeNav === item.key;
              const isDisabled = item.disabled;
              return (
                <button
                  key={item.key}
                  type="button"
                  disabled={isDisabled}
                  onClick={() => handleNavChange(item.key)}
                  className={cn(
                    "w-full px-3 py-1.5 text-left text-sm transition-colors",
                    isDisabled
                      ? "text-muted-foreground cursor-not-allowed"
                      : isActive
                        ? "text-foreground font-semibold"
                        : "text-muted-foreground hover:text-foreground",
                  )}
                >
                  <span className="block">{item.label}</span>
                </button>
              );
            })}
          </div>
        </aside>

        {(activeNav === "assisted-research" || activeNav === "autonomous-research") && (
          <div
            className={cn(
              "relative flex-shrink-0 h-full transition-[width] duration-200 ease-in-out",
              sessionsExpanded ? "w-56" : "w-0",
            )}
          >
            <div
              className={cn(
                "overflow-hidden transition-[width,opacity] duration-200 ease-in-out h-full",
                sessionsExpanded ? "w-56 opacity-100" : "w-0 opacity-0",
              )}
            >
              <SectionsSidebar
                sections={activeNav === "autonomous-research" ? autoSections : researchSections}
                activeSection={
                  activeNav === "autonomous-research" ? activeAutoSection : activeResearchSection
                }
                onSelectSection={
                  activeNav === "autonomous-research"
                    ? setActiveAutoSection
                    : setActiveResearchSection
                }
              />
            </div>
          </div>
        )}
        <MainContent
          assistedSection={activeResearchSection}
          autonomousSection={activeAutoSection}
          activeFeature={activeFeature}
          activeNav={activeNav}
          assistedResearchProps={{
            workflowTree,
            activeNodeId,
            setActiveNodeId,
            addWorkflowNode,
            updateNodeSnapshot,
            resetDownstreamSessions,
            onNavigate: handleNavigate,
          }}
          sessionsExpanded={sessionsExpanded}
          onToggleSessions={handleToggleSessions}
          onCreateSection={handleCreateSection}
          onUpdateSectionTitle={handleUpdateSectionTitle}
          onRefreshAutoSessions={fetchAutoSections}
        />
      </div>
    </div>
  );

  if (eeComponents) {
    return <eeComponents.AuthGuard>{appContent}</eeComponents.AuthGuard>;
  }

  return appContent;
}
