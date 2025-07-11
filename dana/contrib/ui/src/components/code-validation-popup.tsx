import { useState, useCallback } from 'react';
import { apiService } from '@/lib/api';
import type { CodeValidationResponse } from '@/lib/api';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { CheckCircle, AlertCircle, X, Loader2, Wrench, Check } from 'lucide-react';

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
        toast.success('Code fixes generated successfully!');
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
      console.log('Applying fix:', {
        fixedCode,
        appliedFixes,
        onCodeChangeType: typeof onCodeChange,
        onCodeChangeFunction: onCodeChange.toString(),
      });

      // Call the onChange function with the fixed code
      onCodeChange(fixedCode);

      // Add a small delay to ensure the editor updates
      setTimeout(() => {
        console.log('Fix applied, popup closing...');
        toast.success(`Applied ${appliedFixes.length} fix(es): ${appliedFixes.join(', ')}`);
        onClose();
        setFixedCode(null);
        setAppliedFixes([]);
        setShowPreview(false);
      }, 100);
    } else {
      console.log('No fixed code available to apply');
    }
  }, [fixedCode, appliedFixes, onCodeChange, onClose]);

  const handleValidate = () => {
    validateCode();
  };

  if (!isOpen) return null;

  return (
    <div className="flex fixed inset-0 z-50 justify-center items-center bg-black/50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4 max-h-[80vh] flex flex-col">
        {/* Header */}
        <div className="flex justify-between items-center p-4 border-b">
          <h3 className="text-lg font-semibold">Code Validation</h3>
          <Button variant="ghost" size="sm" onClick={onClose} className="p-0 w-8 h-8">
            <X className="w-4 h-4" />
          </Button>
        </div>

        {/* Content (scrollable) */}
        <div className="overflow-y-auto flex-1 p-4 space-y-4">
          {/* Validation Status */}
          <div className="flex justify-between items-center">
            <div className="flex gap-2 items-center">
              {isValidating ? (
                <Loader2 className="w-4 h-4 text-blue-500 animate-spin" />
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
              <div className="overflow-y-auto space-y-2 max-h-40">
                {result.errors.map((error, index) => (
                  <div
                    key={index}
                    className="flex gap-2 items-start p-2 text-xs bg-red-50 rounded border border-red-200"
                  >
                    <AlertCircle className="w-3 h-3 text-red-500 mt-0.5 flex-shrink-0" />
                    <div className="flex-1">
                      <div className="flex gap-2 items-center">
                        <span className="font-medium text-red-700">Syntax Error</span>
                        <Badge variant="destructive" className="text-xs">
                          {error.severity}
                        </Badge>
                      </div>
                      <pre className="mt-1 font-mono text-xs text-red-600 whitespace-pre-wrap">
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
              <div className="overflow-y-auto space-y-2 max-h-32">
                {result.suggestions.slice(0, 2).map((suggestion, index) => (
                  <div
                    key={index}
                    className="flex gap-2 items-start p-2 text-xs bg-blue-50 rounded border border-blue-200"
                  >
                    <div className="flex-1">
                      <p className="text-blue-600">{suggestion.message}</p>
                    </div>
                  </div>
                ))}
                {result.suggestions.length > 2 && (
                  <p className="text-xs text-center text-gray-500">
                    +{result.suggestions.length - 2} more suggestions
                  </p>
                )}
              </div>
            </div>
          )}

          {/* Code Preview */}
          {showPreview && fixedCode && (
            <div className="p-4 bg-gray-50 border-t">
              <div className="flex justify-between items-center mb-2">
                <h4 className="text-sm font-medium text-green-700">Fixed Code Preview</h4>
                <Badge variant="secondary" className="text-xs text-green-700 bg-green-100">
                  {appliedFixes.length} fix(es) applied
                </Badge>
              </div>
              <div className="space-y-2">
                <div className="text-xs text-green-600">
                  Applied fixes: {appliedFixes.join(', ')}
                </div>
                <div className="overflow-y-auto p-2 max-h-32 bg-white rounded border">
                  <pre className="font-mono text-xs text-gray-800 whitespace-pre-wrap">
                    {fixedCode}
                  </pre>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer (sticky) */}
        <div className="flex sticky right-0 bottom-0 left-0 z-10 justify-between items-center p-4 bg-gray-50 border-t">
          <Button variant="outline" size="sm" onClick={onClose}>
            Close
          </Button>

          <div className="flex gap-2">
            {/* Apply Fix Button - Show whenever there's fixed code available */}
            {fixedCode && (
              <Button
                variant="default"
                size="sm"
                onClick={applyFix}
                className="text-white bg-green-600 hover:bg-green-700"
              >
                <Check className="mr-2 w-4 h-4" />
                Apply Fix ({appliedFixes.length} changes)
              </Button>
            )}

            {/* Auto Fix Button - Always show when there are errors and no fixed code */}
            {result?.errors.length && !fixedCode && (
              <Button variant="default" size="sm" onClick={fixCode} disabled={isFixing}>
                {isFixing ? (
                  <Loader2 className="mr-2 w-4 h-4 animate-spin" />
                ) : (
                  <Wrench className="mr-2 w-4 h-4" />
                )}
                {isFixing ? 'Fixing...' : 'Auto Fix'}
              </Button>
            )}

            {/* Retry Fix Button - Show when there's fixed code but user wants to try again */}
            {fixedCode && result?.errors.length && (
              <Button variant="outline" size="sm" onClick={fixCode} disabled={isFixing}>
                {isFixing ? (
                  <Loader2 className="mr-2 w-4 h-4 animate-spin" />
                ) : (
                  <Wrench className="mr-2 w-4 h-4" />
                )}
                Try Again
              </Button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
