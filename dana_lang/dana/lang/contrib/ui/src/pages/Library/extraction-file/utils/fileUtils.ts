export const getFileExtension = (fileName: string): string => {
  return fileName.split('.').pop()?.toLowerCase() || '';
};

export const getFileType = (fileName: string) => {
  const extension = getFileExtension(fileName);

  return {
    isPdf: extension === 'pdf',
    isExcel: extension === 'xlsx' || extension === 'xls' || extension === 'csv',
    isText: extension === 'txt',
    isDocx: extension === 'docx' || extension === 'doc',
    isImage: extension === 'png' || extension === 'jpg' || extension === 'jpeg',
    extension,
  };
};

export const hasPreviewPane = (fileName: string): boolean => {
  const { isPdf, isText, isDocx, isImage } = getFileType(fileName);
  return isPdf || isText || isDocx || isImage;
};
