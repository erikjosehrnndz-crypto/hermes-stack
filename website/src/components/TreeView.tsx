import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';

type TreeNode = {
  name: string;
  type: 'file' | 'directory';
  children?: TreeNode[];
};

interface Props {
  nodes: TreeNode[];
}

const ChevronIcon: React.FC<{ open: boolean }> = ({ open }) => (
  <svg className={`chevron ${open ? 'open' : ''}`} viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5">
    <path d="M6 4l4 4-4 4" />
  </svg>
);

const FolderIcon: React.FC = () => (
  <svg className="folder-icon" viewBox="0 0 20 20" fill="currentColor">
    <path d="M2 6a2 2 0 012-2h5l2 2h5a2 2 0 012 2v6a2 2 0 01-2 2H4a2 2 0 01-2-2V6z" />
  </svg>
);

const FileIcon: React.FC = () => (
  <svg className="file-icon" viewBox="0 0 20 20" fill="currentColor">
    <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clipRule="evenodd" />
  </svg>
);

const TreeItem: React.FC<{ node: TreeNode; depth: number }> = ({ node, depth }) => {
  const [open, setOpen] = React.useState(depth === 0);
  const isDir = node.type === 'directory';
  const hasChildren = isDir && node.children && node.children.length > 0;

  return (
    <div>
      <div
        className={`tree-item ${isDir ? 'tree-item-dir' : 'tree-item-file'}`}
        style={{ paddingLeft: depth * 20 + 8 }}
        onClick={() => hasChildren && setOpen(!open)}
      >
        {hasChildren ? <ChevronIcon open={open} /> : <span style={{ width: 18, display: 'inline-block' }} />}
        {isDir ? <FolderIcon /> : <FileIcon />}
        <span>{node.name}</span>
      </div>
      {hasChildren && (
        <AnimatePresence initial={false}>
          {open && (
            <motion.div
              key="content"
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.15, ease: 'easeInOut' }}
              style={{ overflow: 'hidden' }}
            >
              {node.children!.map((child, i) => (
                <TreeItem key={child.name + i} node={child} depth={depth + 1} />
              ))}
            </motion.div>
          )}
        </AnimatePresence>
      )}
    </div>
  );
};

const TreeView: React.FC<Props> = ({ nodes }) => {
  return (
    <div className="tree-container">
      <div className="tree-toolbar">
        <div className="tree-toolbar-dots">
          <span style={{ background: '#ef4444' }} />
          <span style={{ background: '#eab308' }} />
          <span style={{ background: '#22c55e' }} />
        </div>
        <div className="tree-toolbar-title">
          ~/hermes-stack
        </div>
        <div style={{ width: 52 }} />
      </div>
      <div className="tree-body">
        {nodes.map((node, idx) => (
          <TreeItem key={node.name + idx} node={node} depth={0} />
        ))}
      </div>
    </div>
  );
};

export default TreeView;
