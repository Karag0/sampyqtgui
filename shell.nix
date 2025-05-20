{ pkgs ? import <nixpkgs> {} }:
pkgs.mkShell {
  packages = [ pkgs.python312Full ];

  env = {
    LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath [
      pkgs.gcc14
      pkgs.zlib
      pkgs.glibc
      pkgs.libxkbcommon
      pkgs.fontconfig
      pkgs.freetype
      pkgs.zstd
      pkgs.dbus
      pkgs.libGL
      pkgs.xorg.libX11
      pkgs.mesa
      pkgs.wayland
      pkgs.xwayland
      pkgs.glib
      pkgs.pulseaudio
      pkgs.krb5
      pkgs.gst_all_1.gst-plugins-base
      pkgs.gst_all_1.gst-plugins-good
      pkgs.gst_all_1.gst-plugins-bad
      pkgs.gst_all_1.gst-plugins-ugly
      pkgs.ffmpeg
      pkgs.qt6.qtbase
      pkgs.pipewire
      pkgs.libvdpau
      pkgs.vulkan-loader
      pkgs.libva
    ];
  };
}