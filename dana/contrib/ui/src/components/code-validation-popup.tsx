import { useState, useCallback } from 'react';
import { apiService } from '@/lib/api';
import type { CodeValidationResponse } from '@/lib/api';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { CheckCircle, AlertCircle, X, Loader2, Wrench } from 'lucide-react';

interface CodeValidationPopupProps {
  code: string;
  onCodeChange: (code: string) => void;
  isOpen: boolean;
  onClose: () => void;
  validationResult?: CodeValidationResponse | null;
}

export const CodeValidationPopup = ({
  code,
  onCodeChange,
  isOpen,
  onClose,
  validationResult: externalValidationResult,
}: CodeValidationPopupProps) => {
  const [validationResult, setValidationResult] = useState<CodeValidationResponse | null>(null);
  const [isValidating, setIsValidating] = useState(false);
  const [isFixing, setIsFixing] = useState(false);

  // Use external validation result if provided
  const result =
    externalValidationResult !== undefined ? externalValidationResult : validationResult;

  const validateCode = useCallback(async () => {
    if (!code.trim()) {
      setValidationResult(null);
      return;
    }
    setIsValidating(true);
    try {
      const result = await apiService.validateCode({
        code,
        agent_name: 'Custom Agent',
        description: 'Agent created via UI',
      });
      setValidationResult(result);
      if (!result.is_valid && result.errors.length > 0) {
        toast.error(`${result.errors.length} validation error(s) found`);
      } else if (result.is_valid) {
        toast.success('Code is valid!');
      }
    } catch (error) {
      console.error('Validation failed:', error);
      toast.error('Failed to validate code');
    } finally {
      setIsValidating(false);
    }
  }, [code]);

  const [fixedCode, setFixedCode] = useState<string | null>(null);
  const [appliedFixes, setAppliedFixes] = useState<string[]>([]);
  const [showPreview, setShowPreview] = useState(false);

  const fixCode = useCallback(async () => {
    if (!result?.errors.length) return;
    setIsFixing(true);
    try {
      const fixResult = await apiService.fixCode({
        code,
        errors: result.errors,
        agent_name: 'Custom Agent',
        description: 'Agent created via UI',
      });
      if (fixResult.success && fixResult.fixed_code) {
        setFixedCode(fixResult.fixed_code);
        setAppliedFixes(fixResult.applied_fixes);
        setShowPreview(true);
      } else {
        toast.error('Failed to fix code automatically');
      }
    } catch (error) {
      console.error('Auto-fix failed:', error);
      toast.error('Failed to fix code automatically');
    } finally {
      setIsFixing(false);
    }
  }, [code, result?.errors]);

  const applyFix = useCallback(() => {
    if (fixedCode) {
      onCodeChange(fixedCode);
      toast.success(`Applied ${appliedFixes.length} fix(es): ${appliedFixes.join(', ')}`);
      onClose();
      setFixedCode(null);
      setAppliedFixes([]);
      setShowPreview(false);
    }
  }, [fixedCode, appliedFixes, onCodeChange, onClose]);

  const handleValidate = () => {
    validateCode();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4 max-h-[80vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b">
          <h3 className="text-lg font-semibold">Code Validation</h3>
          <Button variant="ghost" size="sm" onClick={onClose} className="h-8 w-8 p-0">
            <X className="h-4 w-4" />
          </Button>
        </div>

        {/* Content */}
        <div className="p-4 space-y-4">
          {/* Validation Status */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              {isValidating ? (
                <Loader2 className="w-4 h-4 animate-spin text-blue-500" />
              ) : result?.is_valid ? (
                <CheckCircle className="w-4 h-4 text-green-500" />
              ) : result ? (
                <AlertCircle className="w-4 h-4 text-red-500" />
              ) : (
                <AlertCircle className="w-4 h-4 text-gray-400" />
              )}
              <span className="text-sm font-medium">
                {isValidating
                  ? 'Validating...'
                  : result?.is_valid
                    ? 'Code is valid'
                    : result
                      ? `${result.errors.length} error(s) found`
                      : 'Click validate to check code'}
              </span>
            </div>

            {!externalValidationResult && (
              <Button variant="outline" size="sm" onClick={validateCode} disabled={isValidating}>
                {isValidating ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Validate'}
              </Button>
            )}
          </div>

          {/* Errors Summary */}
          {result?.errors.length && (
            <div className="space-y-2">
              <h4 className="text-sm font-medium text-red-700">Errors</h4>
              <div className="space-y-2 max-h-40 overflow-y-auto">
                {result.errors.map((error, index) => (
                  <div
                    key={index}
                    className="flex items-start gap-2 p-2 bg-red-50 border border-red-200 rounded text-xs"
                  >
                    <AlertCircle className="w-3 h-3 text-red-500 mt-0.5 flex-shrink-0" />
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-red-700">Syntax Error</span>
                        <Badge variant="destructive" className="text-xs">
                          {error.severity}
                        </Badge>
                      </div>
                      <pre className="text-red-600 mt-1 text-xs whitespace-pre-wrap font-mono">
                        {error.message}
                      </pre>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Suggestions Summary */}
          {result?.suggestions.length && (
            <div className="space-y-2">
              <h4 className="text-sm font-medium text-blue-700">Suggestions</h4>
              <div className="space-y-2 max-h-32 overflow-y-auto">
                {result.suggestions.slice(0, 2).map((suggestion, index) => (
                  <div
                    key={index}
                    className="flex items-start gap-2 p-2 bg-blue-50 border border-blue-200 rounded text-xs"
                  >
                    <div className="flex-1">
                      <p className="text-blue-600">{suggestion.message}</p>
                    </div>
                  </div>
                ))}
                {result.suggestions.length > 2 && (
                  <p className="text-xs text-gray-500 text-center">
                    +{result.suggestions.length - 2} more suggestions
                  </p>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Code Preview */}
        {showPreview && fixedCode && (
          <div className="p-4 border-t bg-gray-50">
            <h4 className="text-sm font-medium text-green-700 mb-2">Fixed Code Preview</h4>
            <div className="space-y-2">
              <div className="text-xs text-green-600">Applied fixes: {appliedFixes.join(', ')}</div>
              <div className="bg-white border rounded p-2 max-h-32 overflow-y-auto">
                <pre className="text-xs font-mono text-gray-800 whitespace-pre-wrap">
                  {fixedCode}
                </pre>
              </div>
            </div>
          </div>
        )}

        {/* Footer */}
        <div className="flex items-center justify-between p-4 border-t bg-gray-50">
          <Button variant="outline" size="sm" onClick={onClose}>
            Close
          </Button>

          <div className="flex gap-2">
            {showPreview && fixedCode && (
              <Button variant="default" size="sm" onClick={applyFix}>
                Apply Fix
              </Button>
            )}

            {result?.errors.length && !isFixing && !showPreview && (
              <Button variant="default" size="sm" onClick={fixCode} disabled={isFixing}>
                {isFixing ? (
                  <Loader2 className="w-4 h-4 animate-spin mr-2" />
                ) : (
                  <Wrench className="w-4 h-4 mr-2" />
                )}
                Auto Fix
              </Button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
