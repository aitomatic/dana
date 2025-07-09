import { cn } from "@/lib/utils";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Edit } from "iconoir-react";
import { AgentEditor } from "@/components/agent-editor";
import { CloudUpload } from "iconoir-react";
import { useState } from "react";

const placeholder = `e.g.

# Create the complete AI-powered analysis pipeline

def create_action_plan(ai_analysis):
      # Convert AI insights into actionable recommendations
      prompt = "Based on this analysis, create an action plan: " + ai_analysis
      return reason(prompt, {
        "temperature": 0.5,
        "format": "structured"
      })

# Create the complete AI-powered analysis pipeline
business_intelligence_pipeline = extract_metrics | format_business_summary | analyze_with_ai | create_action_plan

# Example usage with sample data
sample_data = {
    "sales": [1200, 1500, 980, 2100, 1800],
    "ratings": [4.2, 4.5, 3.8, 4.7, 4.1],
    "products": ["Widget A", "Widget B", "Widget C", "Widget D", "Widget E"],
    "period": "Q1 2024"
}`;

export function GeneralAgentPage({
  form,
  watch,
  isDragOver,
  fileInputRef,
  handleFileInputChange,
  triggerFileInput,
}: {
  form: any;
  watch: any;
  isDragOver: boolean;
  fileInputRef: any;
  handleFileInputChange: any;
  triggerFileInput: any;
}) {
  const [isEditingDescription, setIsEditingDescription] = useState(false);

  const { register, setValue, formState } = form;
  const isDisabled = !formState.isValid;

  const avatar = watch("avatar");
  const danaCode = watch("general_agent_config.dana_code");

  return (
    <div
      className={cn(
        "flex w-full flex-col h-[calc(100vh-80px)] gap-4 px-6 bg-gray-50",
        isDragOver && "opacity-50"
      )}
    >
      <div className="flex flex-row gap-4 h-full">
        <div className="flex flex-col justify-between w-[320px] gap-4 pt-4">
          <div className="flex flex-col gap-4">
            <div className="flex flex-col gap-4 p-4 rounded-xl border border-gray-200 dark:border-gray-300 bg-background">
              <img
                src={`/static/agent-avatar${avatar}`}
                alt="agent-placeholder"
                className="rounded-full size-10"
              />
              <div className="flex flex-col gap-1">
                <input
                  className="py-1 w-full text-xl font-semibold text-gray-900 border-b border-gray-900 bg-background border-l-none border-r-none border-t-none focus:outline-none placeholder:text-gray-300"
                  {...register("name", { required: true })}
                  id="name"
                  data-testid="name"
                  placeholder="Agent Name"
                />
              </div>
              <div className="flex flex-col gap-1 h-full">
                {isEditingDescription ? (
                  <div className="flex flex-col gap-1">
                    <Label className="text-sm font-semibold text-gray-600">Description</Label>
                    <Textarea
                      {...register("description")}
                      id="description"
                      data-testid="description"
                      placeholder="Describe what can the tool do. E.g. search the web, analyse data, summarise content"
                      className="bg-background min-h-22 border border-gray-300 rounded-lg p-2.5 text-sm text-gray-900 focus:outline-none resize-none"
                    />
                  </div>
                ) : (
                  <div className="flex flex-col gap-2">
                    <span className="text-sm text-gray-300">(no description)</span>
                    <Button
                      variant="tertiary"
                      className="gap-2 w-max"
                      onClick={() => setIsEditingDescription(true)}
                    >
                      <Edit className="text-gray-600" width={18} height={18} strokeWidth={2} />
                      <span className="text-sm text-gray-600">Add description</span>
                    </Button>
                  </div>
                )}
              </div>
            </div>
            <div className="flex flex-col gap-2 h-full">
              <span className="text-sm font-medium text-gray-600">Resources</span>
              {/* <FileSelection /> */}
            </div>
          </div>
        </div>
        {/* Agent Configuration */}
        <div className="flex flex-col w-[calc(100vw-380px)] h-full gap-2 pt-4">
          <div className="flex flex-col gap-2 h-full">
            <div className="flex flex-row gap-1 justify-between">
              <div className="flex flex-col gap-1">
                <Label className="text-sm font-semibold text-gray-900">Agent Configuration</Label>
                <span className="text-sm text-gray-600">Use DANA to configure your agent</span>
              </div>
              <input
                type="file"
                accept=".na"
                ref={fileInputRef}
                onChange={handleFileInputChange}
                className="hidden"
              />
              <div className="flex gap-2 items-center">
                <Button
                  leftSection={<CloudUpload />}
                  variant="outline"
                  className="w-max bg-background"
                  onClick={(e) => {
                    e.preventDefault();
                    triggerFileInput();
                  }}
                >
                  Upload .na file
                </Button>
              </div>
            </div>

            <div className="flex-1 min-h-0">
              <AgentEditor
                value={
                  danaCode ??
                  'query="User query" \n response = reason(f"Help me to answer the question: {query}")'
                }
                onChange={(value) => {
                  setValue("general_agent_config.dana_code", value);
                }}
                placeholder={placeholder}
                onSave={() => {}}
              />
            </div>
          </div>
        </div>
      </div>

      <div className="flex justify-end">
        <Button
          size="lg"
          disabled={isDisabled}
          className="gap-2 w-max"
          onClick={() => {
            setValue("step", "select-knowledge");
          }}
        >
          Create Agent
        </Button>
      </div>
    </div>
  );
}
