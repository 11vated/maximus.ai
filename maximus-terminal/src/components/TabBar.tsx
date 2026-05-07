import { useTerminalStore } from '../store/useTerminalStore';
import { FiPlus, FiX, FiMessageSquare } from 'react-icons/fi';

export function TabBar() {
  const {
    tabs,
    activeTabId,
    addTab,
    closeTab,
    switchTab,
  } = useTerminalStore();

  const handleAddTab = () => {
    addTab(`Session ${tabs.length + 1}`);
  };

  const handleTabClick = (tabId: string) => {
    switchTab(tabId);
  };

  const handleCloseTab = (e: React.MouseEvent, tabId: string) => {
    e.stopPropagation();
    closeTab(tabId);
  };

  return (
    <div className="flex items-center bg-gray-900 border-b border-gray-700 h-10 px-2">
      <div className="flex items-center space-x-1 overflow-x-auto flex-1">
        {tabs.map((tab) => (
          <div
            key={tab.id}
            onClick={() => handleTabClick(tab.id)}
            className={`
              flex items-center space-x-2 px-4 py-2 rounded-t-lg cursor-pointer
              transition-all duration-200 min-w-[120px] max-w-[200px]
              ${tab.id === activeTabId
                ? 'bg-gray-800 text-green-400 border-t-2 border-green-400'
                : 'bg-gray-900 text-gray-400 hover:bg-gray-800'
              }
            `}
          >
            <FiMessageSquare className="w-4 h-4 flex-shrink-0" />

            <span className="text-sm truncate flex-1">
              {tab.title}
              {tab.unreadCount > 0 && (
                <span className="ml-2 bg-red-500 text-white text-xs rounded-full px-1.5 py-0.5">
                  {tab.unreadCount}
                </span>
              )}
            </span>

            {tabs.length > 1 && (
              <button
                onClick={(e) => handleCloseTab(e, tab.id)}
                className="hover:text-red-400 transition-colors flex-shrink-0"
              >
                <FiX className="w-3.5 h-3.5" />
              </button>
            )}
          </div>
        ))}
      </div>

      <button
        onClick={handleAddTab}
        className="ml-2 p-2 hover:bg-gray-800 rounded transition-colors text-gray-400 hover:text-green-400"
        title="New Tab"
      >
        <FiPlus className="w-4 h-4" />
      </button>
    </div>
  );
}
