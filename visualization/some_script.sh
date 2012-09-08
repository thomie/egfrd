BASE=$HOME/.config/ParaView
SCRIPTS=$BASE/ParaView/Plugins
mkdir -p $SCRIPTS
cp -v tensorGlyph.xml $SCRIPTS
cp -v tensorGlyphWithCustomSource.xml $SCRIPTS
if [ ! -d $BASE/ParaView3.4 ];then
  ln -s ParaView $BASE/ParaView3.4/
fi
if [ ! -d $BASE/ParaView3.6 ];then
  ln -s ParaView $BASE/ParaView3.6/
fi
if [ ! -d $BASE/ParaView3.8 ];then
  ln -s ParaView $BASE/ParaView3.8
fi
