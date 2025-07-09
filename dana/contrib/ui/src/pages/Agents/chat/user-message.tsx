import FileIcon from "@/components/file-icon";
import { cn } from "@/lib/utils";
import { MarkdownViewerSmall } from "./markdown-viewer";

const FilePreview = ({ file }: { file: any }) => {
  const ext = file?.s3_url?.split(".")?.pop();
  const fileName = file?.s3_url?.split("/").pop();

  return (
    <div className="flex" key={file?.id}>
      <div className="flex justify-between gap-2 p-3 border border-gray-200 rounded-lg dark:border-gray-300 w-max bg-background">
        <div className="flex gap-2">
          <div className="flex items-center justify-center bg-gray-100 rounded-md w-11 h-11">
            <FileIcon ext={ext} />
          </div>
          <div className="flex flex-col text-left max-w-[200px]">
            <span className="text-sm font-medium text-gray-700 truncate">
              {fileName}
            </span>
            <span className="text-sm font-normal text-gray-600 truncate">
              {ext}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

const MessageContent = ({ message }: { message: any }) => {
  const isSplitScreen = false;

  switch (message?.type) {
    case "file":
      const metaData = message?.meta_data || message?.data?.meta_data;
      return (
        <div className="flex flex-col">
          <div
            className={cn(
              "flex gap-1 mb-2 overflow-x-auto scrollbar-hide",
              isSplitScreen
                ? "max-w-full 3xl:max-w-full"
                : "max-w-[630px] 3xl:max-w-[1085px]",
            )}
          >
            {metaData?.files?.map((file: any) => (
              <FilePreview key={file.id} file={file} />
            ))}
          </div>
          <div
            className={cn(
              "flex flex-wrap w-full text-sm xl:text-base font-normal text-gray-900 break-words",
              isSplitScreen
                ? "max-w-full 3xl:max-w-full"
                : "max-w-[630px] 3xl:max-w-[1085px]",
            )}
          >
            <MarkdownViewerSmall>
              {message?.message || message?.data?.message}
            </MarkdownViewerSmall>
          </div>
        </div>
      );
    default:
      return (
        <div
          className={cn(
            "flex flex-wrap w-full text-sm xl:text-base font-normal text-gray-900 break-words",
            isSplitScreen
              ? "max-w-full 3xl:max-w-full"
              : "max-w-[630px] 3xl:max-w-[1085px]",
          )}
        >
          <MarkdownViewerSmall>
            {message?.message || message?.data?.message}
          </MarkdownViewerSmall>
        </div>
      );
  }
};

const UserMessage = ({ message }: any) => {
  return (
    <div className="flex items-start w-full gap-2 px-6 py-4 rounded bg-gray-50">
      <MessageContent message={message} />
    </div>
  );
};

export default UserMessage;
