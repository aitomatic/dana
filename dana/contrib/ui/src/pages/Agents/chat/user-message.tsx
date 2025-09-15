/* eslint-disable @typescript-eslint/no-explicit-any */
import FileIcon from '@/components/file-icon';
import { cn } from '@/lib/utils';
import { HybridRenderer } from './hybrid-renderer';

const FilePreview = ({ file }: { file: any }) => {
  const ext = file?.s3_url?.split('.')?.pop();
  const fileName = file?.s3_url?.split('/').pop();

  return (
    <div className="flex" key={file?.id}>
      <div className="flex gap-2 justify-between p-3 w-max rounded-lg border border-gray-200 dark:border-gray-300 bg-background">
        <div className="flex gap-2">
          <div className="flex justify-center items-center w-11 h-11 bg-gray-100 rounded-md">
            <FileIcon ext={ext} />
          </div>
          <div className="flex flex-col text-left max-w-[200px]">
            <span className="text-sm font-medium text-gray-700 truncate">{fileName}</span>
            <span className="text-sm font-normal text-gray-600 truncate">{ext}</span>
          </div>
        </div>
      </div>
    </div>
  );
};

const MessageContent = ({ message }: { message: any }) => {
  const isSplitScreen = false;

  switch (message?.type) {
    case 'file': {
      const metaData = message?.meta_data || message?.data?.meta_data;
      return (
        <div className="flex flex-col">
          <div
            className={cn(
              'flex overflow-x-auto gap-1 mb-2 scrollbar-hide',
              isSplitScreen ? 'max-w-full 3xl:max-w-full' : 'max-w-[630px] 3xl:max-w-[1085px]',
            )}
          >
            {metaData?.files?.map((file: any) => (
              <FilePreview key={file.id} file={file} />
            ))}
          </div>
          <div
            className={cn(
              'flex flex-wrap w-full text-sm font-normal text-gray-900 break-words xl:text-base',
              isSplitScreen ? 'max-w-full 3xl:max-w-full' : 'max-w-[630px] 3xl:max-w-[1085px]',
            )}
          >
            <HybridRenderer
              content={message?.message || message?.data?.message}
              backgroundContext="user"
            />
          </div>
        </div>
      );
    }

    default:
      return (
        <div
          className={cn(
            'flex flex-wrap w-full text-sm font-normal text-gray-900 break-words xl:text-base',
            isSplitScreen ? 'max-w-full 3xl:max-w-full' : 'max-w-[630px] 3xl:max-w-[1085px]',
          )}
        >
          <HybridRenderer
            content={message?.message || message?.data?.message}
            backgroundContext="user"
          />
        </div>
      );
  }
};

const UserMessage = ({ message }: any) => {
  return (
    <div className="flex gap-2 items-start px-6 py-4 w-full bg-gray-50 rounded">
      <MessageContent message={message} />
    </div>
  );
};

export default UserMessage;
