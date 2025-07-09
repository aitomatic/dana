import { ResourceType } from "@/lib/const";
import { cn } from "@/lib/utils";
import { IconFileStarFilled } from "@tabler/icons-react";
import {
  ChatLinesSolid,
  DatabaseCheck,
  DatabaseScriptPlus,
  NetworkRightSolid,
} from "iconoir-react";

export const FILE_ICONS = {
  folder: "/static/files-icon/folder.svg",
  pdf: "/static/files-icon/file-pdf.svg",
  doc: "/static/files-icon/file-docx.svg",
  docx: "/static/files-icon/file-docx.svg",
  csv: "/static/files-icon/file-csv.svg",
  xlsx: "/static/files-icon/file-csv.svg",
  xls: "/static/files-icon/file-csv.svg",
  txt: "/static/files-icon/file-txt.svg",
  png: "/static/files-icon/file-image.svg",
  jpeg: "/static/files-icon/file-image.svg",
  jpg: "/static/files-icon/file-image.svg",
  html: "/static/files-icon/file-code.svg",
} as const;

interface FileIconProps {
  resource?: {
    name: string;
    resource_type?: "file" | "plan" | "interview" | string;
  };
  ext?: string;
  width?: number;
  height?: number;
  className?: string;
}

const FileIcon = ({ resource, ext: extensionProp, width, height, className }: FileIconProps) => {
  if (resource?.resource_type === ResourceType.PLAN) {
    return (
      <img src="/assets/icon/tree-structure.svg" width={20} height={20} alt="Tree structure icon" />
    );
  }

  if (resource?.resource_type === ResourceType.INTERVIEW) {
    return <ChatLinesSolid className="text-yellow-500" width={20} height={20} />;
  }

  if (resource?.resource_type === ResourceType.PRIO_KNOWLEDGE) {
    return <img src="/assets/icon/table.svg" alt="Table icon" />;
  }

  if (resource?.resource_type === ResourceType.EXPERIENTIAL) {
    return <DatabaseScriptPlus className="text-brand-600" width={20} height={20} strokeWidth={2} />;
  }

  if (resource?.resource_type === ResourceType.MCP) {
    return <IconFileStarFilled className="text-brand-700" width={20} height={20} strokeWidth={2} />;
  }

  if (resource?.resource_type === ResourceType.KNOWLEDGE_BASE) {
    return <NetworkRightSolid className="text-[#F79009]" strokeWidth={2} width={20} height={20} />;
  }

  if (resource?.resource_type === "file" || extensionProp) {
    let ext = extensionProp || resource?.name.split(".").pop()?.toLowerCase() || "";
    if (ext === "vnd.openxmlformats-officedocument.wordprocessingml.document") {
      ext = "docx";
    }
    const iconSrc = FILE_ICONS[ext?.toLowerCase?.() as keyof typeof FILE_ICONS];

    if (!iconSrc) return <img src={FILE_ICONS.folder} alt="Folder icon" className="size-5" />;

    return (
      <div className={cn(`flex w-[20px] h-[20px]`, className)}>
        <img
          src={iconSrc}
          alt={iconSrc}
          width={width || 20}
          height={height || 20}
          className={ext.match(/png|jpeg|jpg/) ? "text-brand-600" : ""}
        />
      </div>
    );
  }

  if (resource?.resource_type === "database") {
    return <DatabaseCheck className="text-blue-600" width={20} height={20} strokeWidth={2} />;
  }

  return <img src={FILE_ICONS.folder} alt="Folder icon" />;
};

export default FileIcon;
