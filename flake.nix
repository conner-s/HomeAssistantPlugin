{
  description = "Dev shell for running the Home Assistant StreamController plugin unit tests";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs = { self, nixpkgs }:
    let
      systems = [ "x86_64-linux" "aarch64-linux" "x86_64-darwin" "aarch64-darwin" ];
      forAllSystems = f: nixpkgs.lib.genAttrs systems (system: f system);
    in
    {
      devShells = forAllSystems (system:
        let
          pkgs = import nixpkgs { inherit system; };

          # Python deps mirror requirements_unittests.txt (websocket-client, PyGObject, loguru).
          pythonEnv = pkgs.python313.withPackages (ps: with ps; [
            pygobject3
            websocket-client
            loguru
            pylint  # mirrors the Pylint CI workflow
          ]);
        in
        {
          default = pkgs.mkShell {
            # The gobject-introspection setup hook walks buildInputs (and their
            # propagated inputs) to assemble GI_TYPELIB_PATH, so the whole GTK4
            # closure — Gtk-4.0, Adw-1, GLib, Pango, PangoCairo, … — is resolvable
            # at import time without hand-listing each typelib.
            nativeBuildInputs = [ pkgs.gobject-introspection ];
            buildInputs = [
              pythonEnv
              pkgs.gtk4
              pkgs.libadwaita
              pkgs.glib
            ];

            shellHook = ''
              echo "Home Assistant plugin test shell — run: python -m unittest -v"
            '';
          };
        });
    };
}
