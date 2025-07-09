import { Xmark } from "iconoir-react";
import { useDanaAgentForm } from "@/hooks/use-dana-agent-form";
import { useDragDrop } from "@/hooks/use-drag-drop";
import { cn } from "@/lib/utils";
import { DragOverComponent } from "@/components/drag-over-component";
import { useNavigate } from "react-router-dom";
import { GeneralAgentPage } from "./general";
import SelectKnowledgePage from "./select-knowledge";
import { IconButton } from "@/components/ui/button";

export function CreateAgentPage() {
  const { form } = useDanaAgentForm();
  const { watch, setValue } = form;
  const navigate = useNavigate();

  const handleFileUpload = (file: File) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      const text = e.target?.result as string;
      setValue("general_agent_config.dana_code", text);
    };
    reader.readAsText(file);
  };

  const { isDragOver, dragOverProps, fileInputRef, handleFileInputChange, triggerFileInput } =
    useDragDrop({
      onFileUpload: handleFileUpload,
      acceptedFileTypes: [".na"],
    });

  const step = watch("step");
  const name = watch("name");

  return (
    <div className="flex flex-col w-full h-full" {...dragOverProps}>
      {isDragOver && <DragOverComponent title="Drag file here" description="(only .na file)" />}
      <div
        className={cn(
          "flex items-center justify-between px-6 py-1 border-b h-[70px]",
          isDragOver && "opacity-50"
        )}
      >
        <div className="flex gap-2 items-center">
          <div className="flex gap-4 items-center">
            <span className="text-xl font-semibold text-gray-900">
              {step === "general" ? "Create Domain-Expert Agent" : name}
            </span>
          </div>
        </div>
        <div className="flex flex-row gap-2 justify-end items-center">
          <IconButton
            variant="ghost"
            onClick={() => {
              navigate("/agents");
            }}
            className="w-max"
            aria-label="Close"
          >
            <Xmark className="text-gray-400 size-6" strokeWidth={2} />
          </IconButton>
        </div>
      </div>
      {step === "general" && (
        <GeneralAgentPage
          form={form}
          watch={watch}
          isDragOver={isDragOver}
          fileInputRef={fileInputRef}
          handleFileInputChange={handleFileInputChange}
          triggerFileInput={triggerFileInput}
        />
      )}
      {step === "select-knowledge" && <SelectKnowledgePage />}
    </div>
  );
}
