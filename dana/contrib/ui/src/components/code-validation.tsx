import { useState, useEffect, useCallback } from 'react';
import { cn } from '@/lib/utils';
import { apiService } from '@/lib/api';
import type { CodeValidationResponse } from '@/lib/api';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  CheckCircle,
  AlertCircle,
  AlertTriangle,
  Lightbulb,
  Wrench,
  Loader2,
  RefreshCw,
} from 'lucide-react';

interface CodeValidationProps {
  code: string;
  onCodeChange: (code: string) => void;
  className?: string;
  autoValidate?: boolean;
  showSuggestions?: boolean;
}

export const CodeValidation = ({
  code,
  onCodeChange,
  className,
  autoValidate = true,
  showSuggestions = true,
}: CodeValidationProps) => {
  const [validationResult, setValidationResult] = useState<CodeValidationResponse | null>(null);
  const [isValidating, setIsValidating] = useState(false);
  const [isFixing, setIsFixing] = useState(false);
  const [lastValidatedCode, setLastValidatedCode] = useState('');

  // Auto-validate when code changes
  useEffect(() => {
    if (autoValidate && code !== lastValidatedCode) {
      const timeoutId = setTimeout(() => {
        validateCode();
      }, 1000); // Debounce validation

      return () => clearTimeout(timeoutId);
    }
  }, [code, autoValidate, lastValidatedCode]);

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
      setLastValidatedCode(code);

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

  const fixCode = useCallback(async () => {
    if (!validationResult?.errors.length) return;

    setIsFixing(true);
    try {
      const result = await apiService.fixCode({
        code,
        errors: validationResult.errors,
        agent_name: 'Custom Agent',
        description: 'Agent created via UI',
      });

      if (result.success && result.fixed_code) {
        onCodeChange(result.fixed_code);
        toast.success(`Fixed ${result.applied_fixes.length} issue(s)`);

        // Re-validate the fixed code
        setTimeout(() => {
          validateCode();
        }, 500);
      } else {
        toast.error('Failed to fix code automatically');
      }
    } catch (error) {
      console.error('Auto-fix failed:', error);
      toast.error('Failed to fix code automatically');
    } finally {
      setIsFixing(false);
    }
  }, [code, validationResult?.errors, onCodeChange, validateCode]);

  const getErrorIcon = (severity: string) => {
    switch (severity) {
      case 'error':
        return <AlertCircle className="w-4 h-4 text-red-500" />;
      case 'warning':
        return <AlertTriangle className="w-4 h-4 text-yellow-500" />;
      default:
        return <AlertCircle className="w-4 h-4 text-gray-500" />;
    }
  };

  const getSuggestionIcon = (type: string) => {
    switch (type) {
      case 'syntax':
        return <Wrench className="w-4 h-4 text-blue-500" />;
      case 'best_practice':
        return <Lightbulb className="w-4 h-4 text-green-500" />;
      case 'performance':
        return <RefreshCw className="w-4 h-4 text-purple-500" />;
      case 'security':
        return <AlertTriangle className="w-4 h-4 text-orange-500" />;
      default:
        return <Lightbulb className="w-4 h-4 text-gray-500" />;
    }
  };

  if (!validationResult && !isValidating) {
    return null;
  }

  return (
    <div className={cn('space-y-4', className)}>
      {/* Validation Status Header */}
      <div className="flex justify-between items-center">
        <div className="flex gap-2 items-center">
          {isValidating ? (
            <Loader2 className="w-4 h-4 text-blue-500 animate-spin" />
          ) : validationResult?.is_valid ? (
            <CheckCircle className="w-4 h-4 text-green-500" />
          ) : (
            <AlertCircle className="w-4 h-4 text-red-500" />
          )}
          <span className="text-sm font-medium">
            {isValidating
              ? 'Validating...'
              : validationResult?.is_valid
                ? 'Code is valid'
                : `${validationResult?.errors.length || 0} error(s) found`}
          </span>
        </div>

        <div className="flex gap-2 items-center">
          <Button variant="outline" size="sm" onClick={validateCode} disabled={isValidating}>
            {isValidating ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <RefreshCw className="w-4 h-4" />
            )}
            Validate
          </Button>

          {validationResult?.errors.length && !isFixing && (
            <Button variant="outline" size="sm" onClick={fixCode} disabled={isFixing}>
              {isFixing ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Wrench className="w-4 h-4" />
              )}
              Auto Fix
            </Button>
          )}
        </div>
      </div>

      {/* Errors Section */}
      {validationResult?.errors.length && (
        <div className="space-y-2">
          <h4 className="text-sm font-medium text-red-700">Errors</h4>
          <div className="space-y-2">
            {validationResult.errors.map((error, index) => (
              <div
                key={index}
                className="flex gap-2 items-start p-3 bg-red-50 rounded-lg border border-red-200"
              >
                {getErrorIcon(error.severity)}
                <div className="flex-1">
                  <div className="flex gap-2 items-center">
                    <span className="text-sm font-medium text-red-700">
                      Line {error.line}, Column {error.column}
                    </span>
                    <Badge variant="destructive" className="text-xs">
                      {error.severity}
                    </Badge>
                  </div>
                  <p className="mt-1 text-sm text-red-600">{error.message}</p>
                  {error.code && (
                    <code className="block p-1 mt-1 text-xs text-red-500 bg-red-100 rounded">
                      {error.code}
                    </code>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Warnings Section */}
      {validationResult?.warnings.length && (
        <div className="space-y-2">
          <h4 className="text-sm font-medium text-yellow-700">Warnings</h4>
          <div className="space-y-2">
            {validationResult.warnings.map((warning, index) => (
              <div
                key={index}
                className="flex gap-2 items-start p-3 bg-yellow-50 rounded-lg border border-yellow-200"
              >
                <AlertTriangle className="w-4 h-4 text-yellow-500 mt-0.5" />
                <div className="flex-1">
                  <div className="flex gap-2 items-center">
                    <span className="text-sm font-medium text-yellow-700">
                      Line {warning.line}, Column {warning.column}
                    </span>
                  </div>
                  <p className="mt-1 text-sm text-yellow-600">{warning.message}</p>
                  {warning.suggestion && (
                    <p className="mt-1 text-sm text-yellow-500">Suggestion: {warning.suggestion}</p>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Suggestions Section */}
      {showSuggestions && validationResult?.suggestions.length && (
        <div className="space-y-2">
          <h4 className="text-sm font-medium text-blue-700">Suggestions</h4>
          <div className="space-y-2">
            {validationResult.suggestions.map((suggestion, index) => (
              <div
                key={index}
                className="flex gap-2 items-start p-3 bg-blue-50 rounded-lg border border-blue-200"
              >
                {getSuggestionIcon(suggestion.type)}
                <div className="flex-1">
                  <div className="flex gap-2 items-center">
                    <span className="text-sm font-medium text-blue-700">
                      {suggestion.type.replace('_', ' ').toUpperCase()}
                    </span>
                    <Badge variant="secondary" className="text-xs">
                      suggestion
                    </Badge>
                  </div>
                  <p className="mt-1 text-sm text-blue-600">{suggestion.message}</p>
                  {suggestion.description && (
                    <p className="mt-1 text-sm text-blue-500">{suggestion.description}</p>
                  )}
                  {suggestion.code && (
                    <code className="block p-1 mt-1 text-xs text-blue-500 bg-blue-100 rounded">
                      {suggestion.code}
                    </code>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
