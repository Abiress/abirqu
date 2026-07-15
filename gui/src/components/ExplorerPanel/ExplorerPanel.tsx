import React, { useState, useRef, useEffect, useCallback } from 'react';
import { listDirectory } from '../../api/commands';

type FileNode = {
  id: string;
  name: string;
  type: 'file' | 'folder';
  extension?: string;
  size?: number;
  children?: FileNode[];
  path?: string;
};

function generateId(): string {
  return Math.random().toString(36).substring(2, 9);
}

async function loadDirectoryAsTree(path?: string): Promise<FileNode[]> {
  try {
    const resp = await listDirectory(path);
    return resp.entries.map((entry) => ({
      id: entry.path,
      name: entry.name,
      type: (entry.is_dir ? 'folder' : 'file') as 'file' | 'folder',
      extension: entry.extension,
      size: entry.size,
      path: entry.path,
      children: entry.is_dir ? [] : undefined,
    }));
  } catch {
    return [];
  }
}

function getFileIcon(name: string, type: 'file' | 'folder', expanded?: boolean): string {
  if (type === 'folder') return expanded ? '📂' : '📁';
  if (name.endsWith('.py')) return '🐍';
  if (name.endsWith('.qasm')) return '⚛️';
  if (name.endsWith('.json')) return '📋';
  if (name.endsWith('.abirqu')) return '🔮';
  return '📄';
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function findAndModify(
  nodes: FileNode[],
  targetId: string,
  modifier: (node: FileNode) => FileNode | null
): FileNode[] {
  return nodes
    .map((node) => {
      if (node.id === targetId) return modifier(node);
      if (node.children) {
        return { ...node, children: findAndModify(node.children, targetId, modifier) };
      }
      return node;
    })
    .filter((n): n is FileNode => n !== null);
}

function addChildToNode(
  nodes: FileNode[],
  parentId: string,
  child: FileNode
): FileNode[] {
  return nodes.map((node) => {
    if (node.id === parentId) {
      return { ...node, children: [...(node.children || []), child] };
    }
    if (node.children) {
      return { ...node, children: addChildToNode(node.children, parentId, child) };
    }
    return node;
  });
}

function setNodeChildren(
  nodes: FileNode[],
  parentId: string,
  children: FileNode[]
): FileNode[] {
  return nodes.map((node) => {
    if (node.id === parentId) {
      return { ...node, children };
    }
    if (node.children) {
      return { ...node, children: setNodeChildren(node.children, parentId, children) };
    }
    return node;
  });
}

function addAtRoot(nodes: FileNode[], child: FileNode): FileNode[] {
  const root = nodes[0];
  if (!root) return [child];
  return [{ ...root, children: [...(root.children || []), child] }];
}

interface ContextMenuState {
  visible: boolean;
  x: number;
  y: number;
  targetId: string | null;
  targetType: 'file' | 'folder' | null;
}

interface TreeNodeProps {
  node: FileNode;
  depth: number;
  selectedId: string | null;
  expandedIds: Set<string>;
  onSelect: (id: string) => void;
  onToggle: (id: string) => void;
  onContextMenu: (e: React.MouseEvent, id: string, type: 'file' | 'folder') => void;
}

function TreeNode({ node, depth, selectedId, expandedIds, onSelect, onToggle, onContextMenu }: TreeNodeProps) {
  const isExpanded = expandedIds.has(node.id);
  const isSelected = selectedId === node.id;
  const isFolder = node.type === 'folder';
  const icon = getFileIcon(node.name, node.type, isExpanded);

  const handleClick = () => {
    if (isFolder) {
      onToggle(node.id);
    } else {
      onSelect(node.id);
    }
  };

  return (
    <div>
      <div
        className={`flex items-center gap-1 px-2 py-0.5 cursor-pointer select-none transition-colors ${
          isSelected
            ? 'bg-[var(--accent-primary)]/15 text-[var(--accent-primary)]'
            : 'text-[var(--text-secondary)] hover:bg-[var(--bg-hover)] hover:text-[var(--text-primary)]'
        }`}
        style={{ paddingLeft: `${depth * 16 + 8}px` }}
        onClick={handleClick}
        onContextMenu={(e) => onContextMenu(e, node.id, node.type)}
      >
        {isFolder && (
          <span className="text-[8px] text-[var(--text-muted)] w-3 text-center select-none">
            {isExpanded ? '▾' : '▸'}
          </span>
        )}
        {!isFolder && <span className="w-3" />}
        <span className="text-xs leading-none">{icon}</span>
        <span className="text-[11px] truncate flex-1">{node.name}</span>
        {node.type === 'file' && node.size !== undefined && (
          <span className="text-[9px] text-[var(--text-muted)] font-mono">
            {formatSize(node.size)}
          </span>
        )}
      </div>
      {isFolder && isExpanded && node.children && (
        <div className="animate-fade-in">
          {node.children.length === 0 ? (
            <div
              className="text-[9px] text-[var(--text-muted)] italic pl-8 py-0.5"
              style={{ paddingLeft: `${(depth + 1) * 16 + 8}px` }}
            >
              Empty folder
            </div>
          ) : (
            node.children.map((child) => (
              <TreeNode
                key={child.id}
                node={child}
                depth={depth + 1}
                selectedId={selectedId}
                expandedIds={expandedIds}
                onSelect={onSelect}
                onToggle={onToggle}
                onContextMenu={onContextMenu}
              />
            ))
          )}
        </div>
      )}
    </div>
  );
}

export default function ExplorerPanel() {
  const [tree, setTree] = useState<FileNode[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(true);
  const [contextMenu, setContextMenu] = useState<ContextMenuState>({
    visible: false,
    x: 0,
    y: 0,
    targetId: null,
    targetType: null,
  });
  const [newFileName, setNewFileName] = useState('');
  const [isCreating, setIsCreating] = useState(false);
  const [creatingType, setCreatingType] = useState<'file' | 'folder'>('file');
  const [renamingId, setRenamingId] = useState<string | null>(null);
  const [renameValue, setRenameValue] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);
  const renameRef = useRef<HTMLInputElement>(null);

  // Load root directory on mount
  useEffect(() => {
    let cancelled = false;
    (async () => {
      const entries = await loadDirectoryAsTree();
      if (!cancelled) {
        setTree(entries);
        setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, []);

  useEffect(() => {
    if (isCreating && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isCreating]);

  useEffect(() => {
    if (renamingId && renameRef.current) {
      renameRef.current.focus();
      renameRef.current.select();
    }
  }, [renamingId]);

  useEffect(() => {
    const handleClick = () => setContextMenu((prev) => ({ ...prev, visible: false }));
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setContextMenu((prev) => ({ ...prev, visible: false }));
        setIsCreating(false);
        setRenamingId(null);
      }
    };
    document.addEventListener('click', handleClick);
    document.addEventListener('keydown', handleKey);
    return () => {
      document.removeEventListener('click', handleClick);
      document.removeEventListener('keydown', handleKey);
    };
  }, []);

  const handleSelect = useCallback((id: string) => {
    setSelectedId(id);
  }, []);

  const handleToggle = useCallback((id: string) => {
    setExpandedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
        // Load children if folder is empty
        const node = findNodeById(tree, id);
        if (node && node.type === 'folder' && node.children && node.children.length === 0 && node.path) {
          loadDirectoryAsTree(node.path).then((children) => {
            setTree((prevTree) => setNodeChildren(prevTree, id, children));
          });
        }
      }
      return next;
    });
  }, [tree]);

  const handleContextMenu = useCallback((e: React.MouseEvent, id: string, type: 'file' | 'folder') => {
    e.preventDefault();
    e.stopPropagation();
    setContextMenu({ visible: true, x: e.clientX, y: e.clientY, targetId: id, targetType: type });
  }, []);

  const handleCreateFile = () => {
    const name = newFileName.trim();
    if (!name) return;

    const ext = name.includes('.') ? name.split('.').pop() : undefined;
    const newNode: FileNode = {
      id: generateId(),
      name,
      type: 'file',
      extension: ext,
      size: 0,
    };

    setTree((prev) => {
      if (contextMenu.targetId && contextMenu.targetType === 'folder') {
        return addChildToNode(prev, contextMenu.targetId, newNode);
      }
      return addAtRoot(prev, newNode);
    });

    setNewFileName('');
    setIsCreating(false);
  };

  const handleCreateFolder = () => {
    const name = newFileName.trim();
    if (!name) return;

    const newNode: FileNode = {
      id: generateId(),
      name,
      type: 'folder',
      children: [],
    };

    setTree((prev) => {
      if (contextMenu.targetId && contextMenu.targetType === 'folder') {
        return addChildToNode(prev, contextMenu.targetId, newNode);
      }
      return addAtRoot(prev, newNode);
    });

    setNewFileName('');
    setIsCreating(false);
  };

  const handleDelete = () => {
    if (!contextMenu.targetId) return;
    setTree((prev) => findAndModify(prev, contextMenu.targetId!, () => null));
    if (selectedId === contextMenu.targetId) setSelectedId(null);
    setContextMenu((prev) => ({ ...prev, visible: false }));
  };

  const handleRename = () => {
    if (!contextMenu.targetId) return;
    setRenamingId(contextMenu.targetId);
    const node = findNodeById(tree, contextMenu.targetId);
    setRenameValue(node?.name || '');
    setContextMenu((prev) => ({ ...prev, visible: false }));
  };

  const handleRenameConfirm = () => {
    if (!renamingId || !renameValue.trim()) {
      setRenamingId(null);
      return;
    }

    const newName = renameValue.trim();
    const ext = newName.includes('.') ? newName.split('.').pop() : undefined;

    setTree((prev) =>
      findAndModify(prev, renamingId, (node) => ({
        ...node,
        name: newName,
        extension: node.type === 'file' ? ext : node.extension,
      }))
    );
    setRenamingId(null);
    setRenameValue('');
  };

  const contextMenuAction = (action: string) => {
    switch (action) {
      case 'rename':
        handleRename();
        break;
      case 'delete':
        handleDelete();
        break;
      case 'new-file':
        setCreatingType('file');
        setIsCreating(true);
        setContextMenu((prev) => ({ ...prev, visible: false }));
        break;
      case 'new-folder':
        setCreatingType('folder');
        setIsCreating(true);
        setContextMenu((prev) => ({ ...prev, visible: false }));
        break;
    }
  };

  const selectedNode = selectedId ? findNodeById(tree, selectedId) : null;

  return (
    <div className="flex flex-col h-full select-none">
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-2 border-b border-[var(--border)]">
        <span className="text-[11px] font-medium text-[var(--text-primary)]">Explorer</span>
        <div className="flex gap-1">
          <button
            onClick={() => { setCreatingType('file'); setIsCreating(true); }}
            className="px-1.5 py-0.5 rounded text-[9px] font-medium bg-[var(--bg-input)] border border-[var(--border)] text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:border-[var(--border-strong)] transition-all"
            title="New File"
          >
            + File
          </button>
          <button
            onClick={() => { setCreatingType('folder'); setIsCreating(true); }}
            className="px-1.5 py-0.5 rounded text-[9px] font-medium bg-[var(--bg-input)] border border-[var(--border)] text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:border-[var(--border-strong)] transition-all"
            title="New Folder"
          >
            + Folder
          </button>
        </div>
      </div>

      {/* New file input */}
      {isCreating && (
        <div className="px-2 py-1.5 border-b border-[var(--border)] animate-fade-in">
          <div className="flex items-center gap-1">
            <span className="text-xs">{creatingType === 'folder' ? '📁' : '📄'}</span>
            <input
              ref={inputRef}
              type="text"
              value={newFileName}
              onChange={(e) => setNewFileName(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  if (creatingType === 'folder') handleCreateFolder();
                  else handleCreateFile();
                }
                if (e.key === 'Escape') setIsCreating(false);
              }}
              onBlur={() => {
                if (!newFileName.trim()) setIsCreating(false);
              }}
              placeholder={creatingType === 'folder' ? 'folder name' : 'filename.ext'}
              className="flex-1 px-1.5 py-0.5 rounded text-[11px] bg-[var(--bg-input)] text-[var(--text-primary)] border border-[var(--border)] focus:border-[var(--accent-primary)] focus:outline-none transition-colors placeholder:text-[var(--text-muted)]"
            />
          </div>
        </div>
      )}

      {/* File tree */}
      <div className="flex-1 overflow-auto py-1">
        {loading ? (
          <div className="flex items-center justify-center h-full text-[var(--text-muted)]">
            <span className="w-3 h-3 border-2 border-[var(--accent-primary)] border-t-transparent rounded-full animate-spin mr-2" />
            <span className="text-[10px]">Loading...</span>
          </div>
        ) : tree.length === 0 ? (
          <div className="flex items-center justify-center h-full text-[var(--text-muted)]">
            <span className="text-[10px]">No files found</span>
          </div>
        ) : (
          tree.map((node) => (
            <TreeNode
              key={node.id}
              node={node}
              depth={0}
              selectedId={selectedId}
              expandedIds={expandedIds}
              onSelect={handleSelect}
              onToggle={handleToggle}
              onContextMenu={handleContextMenu}
            />
          ))
        )}
      </div>

      {/* Status bar */}
      {selectedNode && (
        <div className="px-3 py-1.5 border-t border-[var(--border)] bg-[var(--bg-primary)]">
          <div className="flex items-center gap-2">
            <span className="text-xs">{getFileIcon(selectedNode.name, selectedNode.type)}</span>
            <span className="text-[10px] text-[var(--text-primary)] truncate">{selectedNode.name}</span>
            {selectedNode.type === 'file' && selectedNode.size !== undefined && (
              <span className="text-[9px] text-[var(--text-muted)] ml-auto font-mono">
                {formatSize(selectedNode.size)}
              </span>
            )}
          </div>
        </div>
      )}

      {/* Context menu */}
      {contextMenu.visible && (
        <div
          className="fixed z-50 animate-fade-in"
          style={{ left: contextMenu.x, top: contextMenu.y }}
          onClick={(e) => e.stopPropagation()}
        >
          <div className="bg-[var(--bg-panel)] border border-[var(--border-strong)] rounded-lg shadow-xl py-1 min-w-[140px]">
            <button
              onClick={() => contextMenuAction('new-file')}
              className="w-full text-left px-3 py-1.5 text-[11px] text-[var(--text-secondary)] hover:bg-[var(--bg-hover)] hover:text-[var(--text-primary)] transition-colors flex items-center gap-2"
            >
              <span className="text-xs">📄</span>
              New File
            </button>
            <button
              onClick={() => contextMenuAction('new-folder')}
              className="w-full text-left px-3 py-1.5 text-[11px] text-[var(--text-secondary)] hover:bg-[var(--bg-hover)] hover:text-[var(--text-primary)] transition-colors flex items-center gap-2"
            >
              <span className="text-xs">📁</span>
              New Folder
            </button>
            <div className="my-1 border-t border-[var(--border)]" />
            <button
              onClick={() => contextMenuAction('rename')}
              className="w-full text-left px-3 py-1.5 text-[11px] text-[var(--text-secondary)] hover:bg-[var(--bg-hover)] hover:text-[var(--text-primary)] transition-colors flex items-center gap-2"
            >
              <span className="text-xs">✏️</span>
              Rename
            </button>
            <button
              onClick={() => contextMenuAction('delete')}
              className="w-full text-left px-3 py-1.5 text-[11px] text-[var(--accent-error)] hover:bg-[var(--bg-hover)] transition-colors flex items-center gap-2"
            >
              <span className="text-xs">🗑️</span>
              Delete
            </button>
          </div>
        </div>
      )}

      {/* Inline rename */}
      {renamingId && (
        <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/30">
          <div className="bg-[var(--bg-panel)] border border-[var(--border-strong)] rounded-lg p-3 shadow-xl animate-fade-in">
            <div className="text-[11px] text-[var(--text-primary)] mb-2 font-medium">Rename</div>
            <input
              ref={renameRef}
              type="text"
              value={renameValue}
              onChange={(e) => setRenameValue(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') handleRenameConfirm();
                if (e.key === 'Escape') setRenamingId(null);
              }}
              onBlur={handleRenameConfirm}
              className="w-56 px-2 py-1 rounded text-[11px] bg-[var(--bg-input)] text-[var(--text-primary)] border border-[var(--border)] focus:border-[var(--accent-primary)] focus:outline-none transition-colors"
            />
            <div className="flex gap-1 mt-2 justify-end">
              <button
                onClick={() => setRenamingId(null)}
                className="px-2 py-0.5 rounded text-[9px] bg-[var(--bg-input)] text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleRenameConfirm}
                className="px-2 py-0.5 rounded text-[9px] bg-[var(--accent-primary)] text-white hover:opacity-90 transition-opacity"
              >
                Rename
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function findNodeById(nodes: FileNode[], id: string): FileNode | null {
  for (const node of nodes) {
    if (node.id === id) return node;
    if (node.children) {
      const found = findNodeById(node.children, id);
      if (found) return found;
    }
  }
  return null;
}
