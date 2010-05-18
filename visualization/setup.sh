BASE=$HOME/.config/ParaView
SCRIPTS=$BASE/ParaView/Plugins
mkdir -p $SCRIPTS
cp tensorGlyph.xml $SCRIPTS
cp tensorGlyphCustomSource.xml $SCRIPTS
ln -s ParaView $BASE/ParaView3.4
ln -s ParaView $BASE/ParaView3.6
ln -s ParaView $BASE/ParaView3.8

