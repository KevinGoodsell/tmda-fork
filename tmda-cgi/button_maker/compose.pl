#!/usr/bin/perl

# Copyright (C) 2003 Gre7g Luterman <gre7g@wolfhome.com>
#
# This file is part of TMDA.
#
# TMDA is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.  A copy of this license should
# be included in the file COPYING.
#
# TMDA is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.
#
# You should have received a copy of the GNU General Public License
# along with TMDA; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA

# I would have done this code in Python, but PythonMagic appears to still
# be in its infancy whereas PerlMagic is fairly well established and seems
# to work (although sadly you have to write in Perl to use it).

use Clone qw(clone);
use Image::Magick;
use Getopt::Std;

# Get my dir
if ($0 =~ /^(.*)\/[^\/]+$/) { $MyDir = $1; }
else { $MyDir = "."; }

# Find characters in image
sub FindIndex($font)
{
  my ($font) = @_;
  my $i;

  for ($i = 0; $i < length($font->{"chars"}); $i++)
  {
    $font->{"index"}{substr($font->{"chars"}, $i, 1)} = $i;
  }
}

# Create font specs
my ($font18, $hi18, $font14, $hi14, $small, $fonts);
$font18 =
{
  "chars" =>
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz&.0123456789' ",
  "space" => 25, "linespacing" => 18,
  "font" => "$MyDir/normal.png",
  "mask" => "$MyDir/mask.png", "index" => {},
  "width" =>
    [
      # A-M
      15, 14, 14, 14, 13, 11, 15, 15, 6, 12, 15, 12, 17,
      # N-Z
      15, 15, 13, 15, 15, 13, 14, 15, 15, 19, 14, 15, 14,
      # a-m
      12, 12, 12, 12, 12, 7, 12, 12, 5, 7, 12, 6, 18,
      # n-z
      12, 12, 12, 12, 8, 11, 8, 12, 12, 17, 12, 11, 10,
      # &.0-9'(space)
      16, 8, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 8, 9
    ]
};
&FindIndex($font18);
$hi18 = clone($font18);
$hi18->{"font"} = "$MyDir/highlighted.png";

$font14 =
{
  "chars" =>
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz&.0123456789'-©? ",
  "space" => 25, "linespacing" => 14,
  "font" => "$MyDir/normal14.png",
  "mask" => "$MyDir/mask14.png", "index" => {},
  "width" =>
    [
      # A-M
      11, 10, 10, 10, 9, 8, 10, 10, 4, 8, 11, 9, 12,
      # N-Z
      10, 11, 9, 11, 11, 9, 9, 11, 12, 14, 11, 10, 10,
      # a-m
      8, 9, 8, 8, 9, 5, 8, 8, 4, 4, 9, 4, 13,
      # n-z
      8, 9, 9, 8, 6, 8, 6, 9, 9, 13, 9, 8, 8,
      # &.0-9'-©?(space)
      12, 6, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 4, 4, 13, 8, 5
    ]
};
&FindIndex($font14);
$hi14 = clone($font14);
$hi14->{"font"} = "$MyDir/highlighted14.png";

$small =
{
  "chars" => "ABCDEFGHIJKLMNOPQRSTUVWXYZ ",
  "space" => 15, "linespacing" => 10,
  "font" => "$MyDir/smfont.png",
  "mask" => "$MyDir/smmask.png", "index" => {},
  "width" =>
    [
      # A-M
      9, 9, 9, 9, 9, 8, 10, 10, 5, 8, 10, 9, 11,
      # N-Z?
      10, 10, 9, 10, 10, 9, 9, 10, 10, 12, 10, 10, 10
    ]
};
&FindIndex($small);

# Associate names with fonts
$fonts =
{
  "18" => $font18, "18H" => $hi18, "14" => $font14, "14H" => $hi14,
  "small" => $small
};

# Underline text
# Bleah.  This is WAY too much work!
sub Underline($image, $x, $width, $font)
{
  # Get the passed variables because Perl is dumb
  my ($image, $x, $width, $font) = @_;
  
  # Define local variables because Perl is dumb
  my ($chars, $mask);
  
  $chars = Image::Magick->new();
  $mask = Image::Magick->new();

  # Get base image
  $chars->Read($font->{"font"});
  $mask->Read($font->{"font"});

  # Mask off colors
  $chars->Crop(x=>4, y=>2, width=>1, height=>1);
  $mask->Crop(x=>0, y=>0, width=>1, height=>1);
  
  # Resize
  $chars->Scale(width=>$width, height=>1);
  $mask->Scale(width=>$width + 2, height=>3);

  # Merge
  $image->Composite(image=>$mask, x=>$x, y=>96);
  $image->Composite(image=>$chars, x=>$x + 1, y=>97);

  undef $chars, $mask;
}

# Add text to an image
# (Yes, this is a lot more work than using the PerlMagick annotate feature, but
# for some reason, freetype2 just doesn't produce text that looks as nice.)
sub Compose($image, $str, $x, $y, $font)
{
  # Get the passed variables because Perl is dumb
  my ($image, $str, $x, $y, $font) = @_;

  # Define local variables because Perl is dumb
  my ($chars, $mask, $i, $off, $w);

  $chars = Image::Magick->new();
  $mask = Image::Magick->new();

  # Add each character
  for ($i = 0; $i < length($str); $i++)
  {
    # Get base image
    $chars->Read($font->{"font"});
    $mask->Read($font->{"mask"});

    # Extract character
    $off = $font->{"index"}->{substr($str, $i, 1)};
    $w = $font->{"width"}[$off];
    $chars->Crop(x=>($off * $font->{"space"}), width=>($w + 1));
    $mask->Crop(x=>($off * $font->{"space"}), width=>($w + 1));

    # Place character
    $image->Composite(image=>$chars, mask=>$mask, x=>$x, y=>$y);

    # Move to next
    $x += $w;

    # Clear memory
    @$chars = ();
    @$mask = ();
  }
  
  undef $chars, $mask;
  
  return $x;
}

sub ShowOpt()
{
  print
    "Syntax: composite.pl [-u] [-w <width>] [-i <indent>]\n".
    "          <orig_image> <x> <y> <font> <text> <new_image>\n\n".
    "Where: -u           is an optional switch to indicate underlining\n".
    "       -w           is an optional switch to specify width if resizing is\n".
    "                    required.\n".
    "       -i           is an optional switch to specify the horizontal\n".
    "                    position to indent to on a newline (/) character in\n".
    "                    <text>\n".
    "       <orig_image> is the path to the original image\n".
    "       <x>          is the horizontal position to place the text\n".
    "       <y>          is the vertical position to place the text\n".
    "       <font>       is either 18, 18H, 14, 14H or small\n".
    "       <text>       is a string of text to add to the image\n".
    "       <new_image>  is the path to the new image\n";
  exit;
}

# Q: Why does my Perl code look like I wrote it by banging my head on the
#    punctuation row of the keyboard?

# A: There's two reasons for that, actually...

# Parse options
&ShowOpt if (!getopts("w:ui:"));
&ShowOpt if ($#ARGV != 5);
my ($sfn, $x, $y, $font, $string, $dfn) = @ARGV;
$font = $fonts->{$font};

my ($image, $i, @strings, $x2);
$image = Image::Magick->new();
$image->Read($sfn);
@strings = split(/\//, $string);
$image->Resize
(
  geometry=>$opt_w . "x". ((1 + $#strings) * $font->{"linespacing"}) ."!"
)
  if ($opt_w != 0);

foreach (@strings)
{
  $x2 = &Compose($image, $_, $x, $y, $font);
  $x = $opt_i;
  $y += $font->{"linespacing"};
}
$image->Write($dfn);
