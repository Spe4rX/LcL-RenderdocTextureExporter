###############################################################################
# The MIT License (MIT)
#
# Copyright (c) 2021-2023 Baldur Karlsson
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
###############################################################################
from functools import partial
import os
import renderdoc
import qrenderdoc as qrd
import renderdoc as rd
from typing import Optional

rd = renderdoc
ResourceDescription = rd.ResourceDescription
TextureDescription = rd.ResourceDescription

captureCtx = None
openDirectory = None
textureCount = 0

exportType = None


def get_filename_without_extension(path):
    base_name = os.path.basename(path)  # 获取文件名，包含扩展名
    file_name, extension = os.path.splitext(base_name)  # 分割文件名和扩展名
    return file_name


def get_open_directory():
    global openDirectory
    openDirectory = captureCtx.Extensions().OpenDirectoryName(
        "Save Texture",
        openDirectory,
    )
    if not openDirectory:
        return None

    return openDirectory


def textureHasSliceFace(tex: TextureDescription):
    return tex.arraysize > 1 or tex.depth > 1


def textureHasMipMap(tex: TextureDescription):
    return not (tex.mips == 1 and tex.msSamp <= 1)


def SaveTexture(resourceId, controller, folderName, destType="png"):

    texsave = rd.TextureSave()

    texsave.resourceId = resourceId
    if texsave.resourceId == rd.ResourceId.Null():
        return False

    resourceDesc: rd.ResourceDescription = captureCtx.GetResource(resourceId)
    texture: rd.TextureDescription = captureCtx.GetTexture(resourceId)

    resourceIdStr = str(int(resourceId))

    filename = f"{resourceDesc.name}_{resourceIdStr}"

    texsave.mip = 0
    texsave.slice.depth = 0
    texsave.alpha = rd.AlphaMapping.Preserve
    if destType == "dds":
        texsave.destType = rd.FileType.DDS
    elif destType == "png":
        texsave.destType = rd.FileType.PNG
    elif destType == "jpg":
        texsave.destType = rd.FileType.JPG
    elif destType == "bmp":
        texsave.destType = rd.FileType.BMP
    elif destType == "tga":
        texsave.destType = rd.FileType.TGA
    elif destType == "hdr":
        texsave.destType = rd.FileType.HDR
    elif destType == "exr":
        texsave.destType = rd.FileType.EXR
    folderPath = f"{openDirectory}/{folderName}"

    if not os.path.exists(folderPath):
        os.makedirs(folderPath)

    if textureHasSliceFace(texture):
        if texture.cubemap:
            faces = ["X+", "X-", "Y+", "Y-", "Z+", "Z-"]
            for i in range(texture.arraysize):
                texsave.slice.sliceIndex = i
                outTexPath = f"{folderPath}/{filename}_{faces[i]}.{destType}"
                controller.SaveTexture(texsave, outTexPath)
        else:
            for i in range(texture.depth):
                texsave.slice.sliceIndex = i
                outTexPath = f"{folderPath}/{filename}_{i}.{destType}"
                controller.SaveTexture(texsave, outTexPath)

    else:
        texsave.slice.sliceIndex = 0
        outTexPath = f"{folderPath}/{filename}.{destType}"
        controller.SaveTexture(texsave, outTexPath)

    global textureCount
    textureCount += 1
    return True


# 导出当前Draw的所有Texture
def save_tex(controller: rd.ReplayController,ctx: qrd.CaptureContext):
    global textureCount
    textureCount = 0

    eventID = str(int(captureCtx.CurSelectedEvent()))
    state = controller.GetPipelineState()
    sampleList = state.GetReadOnlyResources(renderdoc.ShaderStage.Fragment)
    for sample in sampleList:
        for boundResource in sample.resources:
            if not SaveTexture(boundResource.resourceId, controller, eventID):
                break
    captureCtx.Extensions().MessageDialog(
        f"Export Complete,Total {textureCount} textures:{openDirectory}",
        "Export Texture",
    )


def texture_callback(ctx: qrd.CaptureContext, data):
    if ctx is None:
        ctx.Extensions().MessageDialog("captureCtx is None", "Export Texture")
        return
    get_open_directory()
    ctx.Replay().AsyncInvoke("", save_tex)


# 导出所有Texture
def save_all_tex(controller: rd.ReplayController):
    captureCtx.Extensions().MessageDialog("1", "3")

    name = captureCtx.GetCaptureFilename()
    name = get_filename_without_extension(name)

    global textureCount
    textureCount = 0
    for tex in captureCtx.GetTextures():
        if exportType:
            if not SaveTexture(tex.resourceId, controller, name, exportType):
                break
    captureCtx.Extensions().MessageDialog(
        f"Export Complete,Total {textureCount} textures:{openDirectory}",
        "Export Texture",
    )


def texture_all_callback():
    if captureCtx is None:
        captureCtx.Extensions().MessageDialog("captureCtx is None", "Export Texture")
        return
    get_open_directory()
    captureCtx.Replay().AsyncInvoke("", save_all_tex)

def texture_all_callback_dds(ctx: qrd.CaptureContext, data):
    global exportType
    exportType = "dds"
    texture_all_callback()

def texture_all_callback_png(ctx: qrd.CaptureContext,data):
    global exportType
    exportType = "png"
    texture_all_callback()

def texture_all_callback_jpg(ctx: qrd.CaptureContext, data):
    global exportType
    exportType = "jpg"
    texture_all_callback()
    
def texture_all_callback_bmp(ctx: qrd.CaptureContext, data):
    global exportType
    exportType = "bmp"
    texture_all_callback()
    
def texture_all_callback_tga(ctx: qrd.CaptureContext, data):
    global exportType
    exportType = "tga"
    texture_all_callback()
    
def texture_all_callback_hdr(ctx: qrd.CaptureContext, data):
    global exportType
    exportType = "hdr"
    texture_all_callback()
    
def texture_all_callback_exr(ctx: qrd.CaptureContext, data):
    global exportType
    exportType = "exr"
    texture_all_callback()


def register(version: str, ctx: qrd.CaptureContext):
    global captureCtx
    captureCtx = ctx
    global openDirectory
    openDirectory = os.path.expanduser("~/Pictures")

    ctx.Extensions().RegisterPanelMenu(
        qrd.PanelMenu.TextureViewer, ["Export Draw Texture"], texture_callback
    )
    ctx.Extensions().RegisterPanelMenu(
        qrd.PanelMenu.TextureViewer, ["Export All Texture(dds)"], texture_all_callback_dds
    )
    ctx.Extensions().RegisterPanelMenu(
        qrd.PanelMenu.TextureViewer, ["Export All Texture(png)"], texture_all_callback_png
    )
    ctx.Extensions().RegisterPanelMenu(
        qrd.PanelMenu.TextureViewer, ["Export All Texture(jpg)"], texture_all_callback_jpg
    )
    ctx.Extensions().RegisterPanelMenu(
        qrd.PanelMenu.TextureViewer, ["Export All Texture(bmp)"], texture_all_callback_bmp
    )
    ctx.Extensions().RegisterPanelMenu(
        qrd.PanelMenu.TextureViewer, ["Export All Texture(tga)"], texture_all_callback_tga
    )
    ctx.Extensions().RegisterPanelMenu(
        qrd.PanelMenu.TextureViewer, ["Export All Texture(hdr)"], texture_all_callback_hdr
    )
    ctx.Extensions().RegisterPanelMenu(
        qrd.PanelMenu.TextureViewer, ["Export All Texture(exr)"], texture_all_callback_exr
    )

def unregister():
    print("Unregistering my extension")
