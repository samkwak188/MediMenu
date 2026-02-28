const MAX_IMAGE_BYTES = 19 * 1024 * 1024;
const MIN_QUALITY = 0.45;

function readFileAsDataURL(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = () => reject(new Error("Failed to read image file."));
    reader.readAsDataURL(file);
  });
}

function getBase64FromDataUrl(dataUrl) {
  const split = dataUrl.split(",", 2);
  if (split.length !== 2) {
    throw new Error("Invalid image data URL.");
  }
  return split[1];
}

function estimateBinarySize(base64String) {
  return Math.floor((base64String.length * 3) / 4);
}

function loadImageElement(file) {
  return new Promise((resolve, reject) => {
    const img = new Image();
    const objectUrl = URL.createObjectURL(file);
    img.onload = () => {
      URL.revokeObjectURL(objectUrl);
      resolve(img);
    };
    img.onerror = () => {
      URL.revokeObjectURL(objectUrl);
      reject(new Error("Selected file is not a valid image."));
    };
    img.src = objectUrl;
  });
}

function toDataUrl(canvas, quality) {
  return canvas.toDataURL("image/jpeg", quality);
}

function resizeDimensions(width, height, maxSide = 2200) {
  if (Math.max(width, height) <= maxSide) {
    return { width, height };
  }
  const scale = maxSide / Math.max(width, height);
  return {
    width: Math.round(width * scale),
    height: Math.round(height * scale),
  };
}

async function compressIfNeeded(file) {
  const image = await loadImageElement(file);
  const dimensions = resizeDimensions(image.width, image.height, 2200);
  const canvas = document.createElement("canvas");
  canvas.width = dimensions.width;
  canvas.height = dimensions.height;

  const ctx = canvas.getContext("2d");
  if (!ctx) {
    throw new Error("Image processing is not available in this browser.");
  }
  ctx.drawImage(image, 0, 0, dimensions.width, dimensions.height);

  let quality = 0.92;
  let dataUrl = toDataUrl(canvas, quality);
  let base64 = getBase64FromDataUrl(dataUrl);

  while (estimateBinarySize(base64) > MAX_IMAGE_BYTES && quality > MIN_QUALITY) {
    quality -= 0.08;
    dataUrl = toDataUrl(canvas, quality);
    base64 = getBase64FromDataUrl(dataUrl);
  }

  if (estimateBinarySize(base64) > MAX_IMAGE_BYTES) {
    throw new Error("Image is too large. Use a clearer but smaller photo.");
  }

  return { base64, mimeType: "image/jpeg" };
}

export async function prepareImageForUpload(file) {
  if (!file) {
    throw new Error("No image selected.");
  }

  if (file.size <= MAX_IMAGE_BYTES) {
    const dataUrl = await readFileAsDataURL(file);
    return {
      base64: getBase64FromDataUrl(dataUrl),
      mimeType: file.type || "image/jpeg",
    };
  }

  return compressIfNeeded(file);
}
