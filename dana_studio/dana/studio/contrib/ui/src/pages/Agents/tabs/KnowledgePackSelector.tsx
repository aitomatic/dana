import { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Search, Check, Xmark } from 'iconoir-react';
import { BookOpen, ExternalLink } from 'lucide-react';
import { toast } from 'sonner';
import { apiService } from '@/lib/api';

interface KnowledgePack {
  id: number;
  kp_metadata?: {
    domain?: string;
    role?: string;
    task?: string;
  };
  status?: string;
  created_at?: string;
}

interface KnowledgePackSelectorProps {
  isOpen: boolean;
  onClose: () => void;
  agentId: number | string;
  currentKpId?: number | null;
  onSelect: (kpId: number) => void;
}

export function KnowledgePackSelector({
  isOpen,
  onClose,
  agentId: _agentId,
  currentKpId: _currentKpId,
  onSelect,
}: KnowledgePackSelectorProps) {
  const [knowledgePacks, setKnowledgePacks] = useState<KnowledgePack[]>([]);
  const [filteredKnowledgePacks, setFilteredKnowledgePacks] = useState<KnowledgePack[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedKpId, setSelectedKpId] = useState<number | null>(null);
  const [isLoadingPacks, setIsLoadingPacks] = useState(false);

  // Fetch knowledge packs when dialog opens
  useEffect(() => {
    if (isOpen) {
      fetchKnowledgePacks();
    }
  }, [isOpen]);

  // Filter knowledge packs based on search term
  useEffect(() => {
    if (!searchTerm.trim()) {
      setFilteredKnowledgePacks(knowledgePacks);
    } else {
      const filtered = knowledgePacks.filter((kp) => {
        const domain = kp.kp_metadata?.domain?.toLowerCase() || '';
        const role = kp.kp_metadata?.role?.toLowerCase() || '';
        const task = kp.kp_metadata?.task?.toLowerCase() || '';
        const search = searchTerm.toLowerCase();
        return domain.includes(search) || role.includes(search) || task.includes(search);
      });
      setFilteredKnowledgePacks(filtered);
    }
  }, [knowledgePacks, searchTerm]);

  const fetchKnowledgePacks = async () => {
    setIsLoadingPacks(true);
    try {
      const response = await apiService.listKnowledgePacks(100, 0);
      if (response && response.data) {
        setKnowledgePacks(response.data);
        setFilteredKnowledgePacks(response.data);
      }
    } catch (error) {
      console.error('Failed to fetch knowledge packs:', error);
      toast.error('Failed to load knowledge packs');
    } finally {
      setIsLoadingPacks(false);
    }
  };

  const handlePackSelect = (kpId: number) => {
    setSelectedKpId(kpId);
  };

  const handleAssign = () => {
    if (selectedKpId === null) {
      toast.error('Please select a knowledge pack');
      return;
    }

    // Call onSelect callback
    onSelect(selectedKpId);
    onClose();
  };

  const handleClose = () => {
    setSearchTerm('');
    setSelectedKpId(null);
    onClose();
  };

  const selectedPack = knowledgePacks.find((kp) => kp.id === selectedKpId);
  const selectedPackMetadata = selectedPack?.kp_metadata || {};

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[600px] max-h-[80vh] flex flex-col">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <BookOpen className="w-5 h-5" />
            Select Knowledge Pack
          </DialogTitle>
        </DialogHeader>

        <div className="flex flex-col gap-4 py-4 flex-1 overflow-hidden">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 w-4 h-4 text-gray-400 transform -translate-y-1/2" />
            <Input
              placeholder="Search knowledge packs..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
            />
          </div>

          {/* Selected Pack Preview */}
          {selectedPack && (
            <div className="p-3 bg-blue-50 rounded-lg border border-blue-200">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-900">Selected:</p>
                  <p className="text-sm text-gray-700 mt-1">
                    {selectedPackMetadata.domain || 'Knowledge Pack'}
                  </p>
                </div>
                <button
                  onClick={() => setSelectedKpId(null)}
                  className="p-1 text-gray-400 hover:text-gray-600 rounded-full hover:bg-blue-100"
                >
                  <Xmark className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}

          {/* Knowledge Packs List */}
          <div className="flex-1 overflow-y-auto border rounded-lg">
            {isLoadingPacks ? (
              <div className="flex justify-center items-center p-8">
                <div className="text-center">
                  <p className="text-sm text-gray-600">Loading knowledge packs...</p>
                </div>
              </div>
            ) : filteredKnowledgePacks.length === 0 ? (
              <div className="flex justify-center items-center p-8">
                <p className="text-sm text-gray-600">
                  {searchTerm ? 'No knowledge packs found matching your search' : 'No knowledge packs available'}
                </p>
              </div>
            ) : (
              <div className="divide-y">
                {filteredKnowledgePacks.map((kp) => {
                  const isSelected = selectedKpId === kp.id;
                  const kpMetadata = kp.kp_metadata || {};

                  return (
                    <div
                      key={kp.id}
                      className={`flex gap-3 p-3 hover:bg-gray-50 cursor-pointer transition-colors ${
                        isSelected ? 'bg-blue-50 border-l-4 border-l-blue-500' : ''
                      }`}
                      onClick={() => handlePackSelect(kp.id)}
                    >
                      <div className="flex-shrink-0 mt-1">
                        {isSelected ? (
                          <div className="flex justify-center items-center w-5 h-5 bg-blue-500 rounded-full">
                            <Check className="w-3 h-3 text-white" />
                          </div>
                        ) : (
                          <div className="w-5 h-5 border-2 border-gray-300 rounded-full" />
                        )}
                      </div>
                      <div className="flex-1">
                        <p className="text-sm font-medium text-gray-900">
                          {kpMetadata.domain || 'Knowledge Pack'}
                        </p>
                        {kp.status && (
                          <p className="text-xs text-gray-500 mt-0.5">Status: {kp.status}</p>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>

        <DialogFooter className="flex justify-between">
          <Button
            variant="outline"
            onClick={() => window.open('/knowledge-center', '_blank')}
          >
            <ExternalLink className="w-4 h-4 mr-2" />
            To Knowledge Packs
          </Button>
          <div className="flex gap-2">
            <Button variant="outline" onClick={handleClose}>
              Cancel
            </Button>
            <Button onClick={handleAssign} disabled={selectedKpId === null}>
              Assign Knowledge Pack
            </Button>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

