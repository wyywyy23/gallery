#!/usr/bin/env bash

SCRIPT_PATH=$(dirname "$0")

# Create a duplicate of each photo, and then minify them
if [[ "$OSTYPE" == "darwin"* && -x "$(command -v mogrify)" ]]; then
  # imagemagick is available
  rm -rf $SCRIPT_PATH/photos/**/*.min.*
  rm -rf $SCRIPT_PATH/photos/**/*.placeholder.*
  python $SCRIPT_PATH/tools/rename.py

  # low res version of image
  python $SCRIPT_PATH/tools/duplicate.py min
  mogrify -resize '1200x1200>' -unsharp 0.5x0.5+0.5+0.008 $SCRIPT_PATH/photos/**/*.min.jpeg &>/dev/null
  mogrify -resize '1200x1200>' -unsharp 0.5x0.5+0.5+0.008 $SCRIPT_PATH/photos/**/*.min.png &>/dev/null
  mogrify -resize '1200x1200>' -unsharp 0.5x0.5+0.5+0.008 $SCRIPT_PATH/photos/**/*.min.jpg &>/dev/null
  mogrify -resize '1200x1200>' -unsharp 0.5x0.5+0.5+0.008 $SCRIPT_PATH/photos/**/*.min.JPEG &>/dev/null
  mogrify -resize '1200x1200>' -unsharp 0.5x0.5+0.5+0.008 $SCRIPT_PATH/photos/**/*.min.PNG &>/dev/null
  mogrify -resize '1200x1200>' -unsharp 0.5x0.5+0.5+0.008 $SCRIPT_PATH/photos/**/*.min.JPG &>/dev/null

  # placeholder image for lazy loading
  python $SCRIPT_PATH/tools/duplicate.py placeholder
  mogrify -resize '32x32>' -unsharp 0.5x0.5+0.5+0.008 $SCRIPT_PATH/photos/**/*.placeholder.jpeg &>/dev/null
  mogrify -resize '32x32>' -unsharp 0.5x0.5+0.5+0.008 $SCRIPT_PATH/photos/**/*.placeholder.png &>/dev/null
  mogrify -resize '32x32>' -unsharp 0.5x0.5+0.5+0.008 $SCRIPT_PATH/photos/**/*.placeholder.jpg &>/dev/null
  mogrify -resize '32x32>' -unsharp 0.5x0.5+0.5+0.008 $SCRIPT_PATH/photos/**/*.placeholder.JPEG &>/dev/null
  mogrify -resize '32x32>' -unsharp 0.5x0.5+0.5+0.008 $SCRIPT_PATH/photos/**/*.placeholder.PNG &>/dev/null
  mogrify -resize '32x32>' -unsharp 0.5x0.5+0.5+0.008 $SCRIPT_PATH/photos/**/*.placeholder.JPG &>/dev/null

elif [[ "$OSTYPE" == "darwin"* && -x "$(command -v sips)" ]]; then
  echo "imagemagick unavailable; using sips without sharpening."
  rm -rf $SCRIPT_PATH/photos/**/*.min.*
  rm -rf $SCRIPT_PATH/photos/**/*.placeholder.*
  python $SCRIPT_PATH/tools/rename.py

  # low res version of image
  python $SCRIPT_PATH/tools/duplicate.py min
  sips -Z 1200 $SCRIPT_PATH/photos/**/*.min.jpeg &>/dev/null
  sips -Z 1200 $SCRIPT_PATH/photos/**/*.min.png &>/dev/null
  sips -Z 1200 $SCRIPT_PATH/photos/**/*.min.jpg &>/dev/null
  sips -Z 1200 $SCRIPT_PATH/photos/**/*.min.JPEG &>/dev/null
  sips -Z 1200 $SCRIPT_PATH/photos/**/*.min.PNG &>/dev/null
  sips -Z 1200 $SCRIPT_PATH/photos/**/*.min.JPG &>/dev/null

  # placeholder image for lazy loading
  python $SCRIPT_PATH/tools/duplicate.py placeholder
  sips -Z 32 $SCRIPT_PATH/photos/**/*.placeholder.jpeg &>/dev/null
  sips -Z 32 $SCRIPT_PATH/photos/**/*.placeholder.png &>/dev/null
  sips -Z 32 $SCRIPT_PATH/photos/**/*.placeholder.jpg &>/dev/null
  sips -Z 32 $SCRIPT_PATH/photos/**/*.placeholder.JPEG &>/dev/null
  sips -Z 32 $SCRIPT_PATH/photos/**/*.placeholder.PNG &>/dev/null
  sips -Z 32 $SCRIPT_PATH/photos/**/*.placeholder.JPG &>/dev/null
fi

if [ -n "$(uname -a | grep Ubuntu)" -a -x "$(command -v mogrify)" ]; then
  # mogrify is available
  rm -rf $SCRIPT_PATH/photos/**/*.min.*
  rm -rf $SCRIPT_PATH/photos/**/*.placeholder.*
  python $SCRIPT_PATH/tools/rename.py

  # low res version of image
  python $SCRIPT_PATH/tools/duplicate.py min
  mogrify -resize '1200x1200>' -unsharp 0.5x0.5+0.5+0.008 $SCRIPT_PATH/photos/**/*.min.jpeg &>/dev/null
  mogrify -resize '1200x1200>' -unsharp 0.5x0.5+0.5+0.008 $SCRIPT_PATH/photos/**/*.min.png &>/dev/null
  mogrify -resize '1200x1200>' -unsharp 0.5x0.5+0.5+0.008 $SCRIPT_PATH/photos/**/*.min.jpg &>/dev/null
  mogrify -resize '1200x1200>' -unsharp 0.5x0.5+0.5+0.008 $SCRIPT_PATH/photos/**/*.min.JPEG &>/dev/null
  mogrify -resize '1200x1200>' -unsharp 0.5x0.5+0.5+0.008 $SCRIPT_PATH/photos/**/*.min.PNG &>/dev/null
  mogrify -resize '1200x1200>' -unsharp 0.5x0.5+0.5+0.008 $SCRIPT_PATH/photos/**/*.min.JPG &>/dev/null

  # placeholder image for lazy loading
  python $SCRIPT_PATH/tools/duplicate.py placeholder
  mogrify -resize '32x32>' -unsharp 0.5x0.5+0.5+0.008 $SCRIPT_PATH/photos/**/*.placeholder.jpeg &>/dev/null
  mogrify -resize '32x32>' -unsharp 0.5x0.5+0.5+0.008 $SCRIPT_PATH/photos/**/*.placeholder.png &>/dev/null
  mogrify -resize '32x32>' -unsharp 0.5x0.5+0.5+0.008 $SCRIPT_PATH/photos/**/*.placeholder.jpg &>/dev/null
  mogrify -resize '32x32>' -unsharp 0.5x0.5+0.5+0.008 $SCRIPT_PATH/photos/**/*.placeholder.JPEG &>/dev/null
  mogrify -resize '32x32>' -unsharp 0.5x0.5+0.5+0.008 $SCRIPT_PATH/photos/**/*.placeholder.PNG &>/dev/null
  mogrify -resize '32x32>' -unsharp 0.5x0.5+0.5+0.008 $SCRIPT_PATH/photos/**/*.placeholder.JPG &>/dev/null

else
  echo "mogrify unavailable; please install imagemagick."
fi  

python $SCRIPT_PATH/tools/setup.py
