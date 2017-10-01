#!/usr/bin/env python3
"""Utility for generating sheets of asset QR codes for Avery L7120 labels."""

import argparse
import os
import tempfile

from PIL import ImageFont, ImageDraw
import fpdf
import qrcode

QR_CODES_PER_PAGE = 35
MARGIN_LEFT = 7.5
MARGIN_TOP = 11
MARGIN_INSIDE = 5
STICKER_WIDTH = 35
STICKER_HEIGHT = 35
FONT_SIZE = 30
FONT_MARGIN = 5

def add_qrcode_to_pdf(pdf, asset_id, width, prefix, tmpdir, idx):
  """Generate the QR Code image and position it on the page.

  Args:
    pdf: fpdf.PDF instance. Assumed to be portrait A4.
    asset_id: integer asset ID.
    width: width to pad the asset ID to.
    prefix: string prefix to prepend to the asset ID in the QR code. Not
      included in the printed ID under the QR code.
    tmpdir: a temporary directory to save generated images to.
    idx: Index of the QR code on the label sheet (left to right, top to bottom,
      starting at zero)
  """
  id_str = '{asset_id:0{width}d}'.format(asset_id=asset_id, width=width)

  qr = qrcode.QRCode(
      version=None, error_correction=qrcode.constants.ERROR_CORRECT_H)
  qr.add_data('{}{}'.format(prefix, id_str))
  qr.make()

  filepath = os.path.join(tmpdir, '{}.png'.format(id_str))

  img = qr.make_image()

  draw = ImageDraw.Draw(img)

  font = ImageFont.truetype('ubuntu.ttf', size=FONT_SIZE)

  text_width, text_height = draw.textsize(id_str, font=font)
  img_width, img_height = img.size
  draw.text(
      ((img_width - text_width)/2, (img_height - text_height - FONT_MARGIN)),
      id_str,
      fill='black',
      font=font)

  img.save(filepath)

  x_pos = MARGIN_LEFT + (idx % 5) * (STICKER_WIDTH + MARGIN_INSIDE)
  y_pos = MARGIN_TOP + (idx // 5) * (STICKER_HEIGHT + MARGIN_INSIDE)

  pdf.image(filepath, x_pos, y_pos, STICKER_WIDTH, STICKER_HEIGHT)


def gen_pdf(outfile, asset_ids, width, prefix):
  """Generate a PDF with sheets of QR codes.

  Args:
    outfile: absolute filepath to write the PDF to.
    asset_ids: list of lists of asset IDs. Each sublist forms a single page, and
      should contain exactly enough codes to fill the page.
    width: width to pad the asset ID to.
    prefix: string prefix to prepend to the asset ID in the QR code. Not
      included in the printed ID under the QR code.
  """
  pdf = fpdf.FPDF()

  with tempfile.TemporaryDirectory() as tmpdir:
    for page_ids in asset_ids:
      pdf.add_page()

      for idx, asset_id in enumerate(page_ids):
        add_qrcode_to_pdf(pdf, asset_id, width, prefix, tmpdir, idx)

  pdf.output(outfile, 'F')


def gen_ids(start_at, num_pages, extra_ids):
  """Generate asset IDs.

  Produces asset IDs including the specific IDs requested, plus contiguous IDs
  from start_at to pad out to full pages.

  A minimum of num_pages pages will be produced; if the number of extra_ids
  takes more than num_pages pages, extra codes will be generated to ensure all
  pages are full.

  Args:
    start_at: Starting asset ID for generated contiguous IDs.
    num_pages: Minimum number of pages to generate.
    extra_ids: Specific asset IDs to generate (for example to replace damaged
      QR codes).

  Returns:
    list of lists of asset IDs, where each sublist contains enough IDs to fill a
    full page.
  """
  ids = extra_ids or []

  ids.extend(
      i + start_at
      for i in range(QR_CODES_PER_PAGE * num_pages - len(ids)))

  return [
      ids[i:i + QR_CODES_PER_PAGE]
      for i in range(0, len(ids), QR_CODES_PER_PAGE)]


def main():
  """Parse arguments and generate the PDF."""
  parser = argparse.ArgumentParser(description='Generate asset QR codes.')
  parser.add_argument('--start_at', type=int, default=1,
                      help='Asset ID to start at')
  parser.add_argument('--num_pages', type=int, default=1,
                      help='Number of pages to generate')
  parser.add_argument('--extra_ids', type=int, action='append',
                      help='Specific asset IDs to generate')
  parser.add_argument('--width', type=int, default=5,
                      help='Length to left-pad asset IDs to with zeros')
  parser.add_argument('--prefix', type=str, default='',
                      help='Prefix to add to generated QR codes')
  parser.add_argument('outfile')
  args = parser.parse_args()

  outfile = os.path.abspath(args.outfile)
  assert os.path.exists(os.path.dirname(outfile))

  gen_pdf(outfile, gen_ids(args.start_at, args.num_pages, args.extra_ids),
          args.width, args.prefix)

if __name__ == '__main__':
  main()
