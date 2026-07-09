type Props = {
  label: string;
  accept?: string;
  file: File | null;
  preview?: string | null;
  onChange: (file: File | null) => void;
};

export function UploadBox({ label, accept = "image/*", file, preview, onChange }: Props) {
  return (
    <label className="upload-box">
      <input
        type="file"
        accept={accept}
        onChange={(event) => onChange(event.target.files?.[0] ?? null)}
      />
      <div className="upload-copy">
        <strong>{label}</strong>
        <span>{file ? file.name : "点击选择图片，支持 jpg/png/webp"}</span>
      </div>
      {preview ? <img src={preview} alt="上传预览" /> : <div className="upload-placeholder">Preview</div>}
    </label>
  );
}
