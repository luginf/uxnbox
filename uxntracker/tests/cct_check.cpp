// Charge un .cct avec le vrai chargeur de ChooChooTracker et affiche ce qu'il a compris.
#include <cstdio>
#include <memory>
#include "project.h"
#include "sid_patch.h"

int main(int argc, char** argv) {
  if (argc < 2) { fprintf(stderr, "usage: cct_check fichier.cct\n"); return 2; }
  auto p = std::make_unique<Project>();
  projectInit(p.get());
  if (projectLoad(p.get(), argv[1])) {
    printf("LOAD FAILED: %s\n", projectFileError);
    return 1;
  }
  printf("title=%s chips=%d tracks=%d tick=%.1f chipType=%d clock=%d\n", p->title, p->chipsCount,
         p->tracksCount, p->tickRate, (int)p->chipType, p->chipSetup.ay.clock);
  printf("groove0: %d %d\n", p->grooves[0].speed[0], p->grooves[0].speed[1]);
  for (int i = 0; i < 8; i++) {
    const Instrument& in = p->instruments[i];
    printf("instrument %d type=%d (1 = AY1, 27 = SID)", i, (int)in.type);
    if ((int)in.type == 27) {
      printf(" name=%s bank=%d schema=%d valid=%d params:", in.chip.sid.presetName,
             (int)in.chip.sid.bankId, (int)in.chip.sid.schema, (int)validSID(in.chip.sid));
      for (int k = 0; k < 25; k++) printf(" %d", (int)in.chip.sid.value[k]);
    }
    printf("\n");
  }
  for (int r = 0; r < 8; r++) {
    printf("song %d:", r);
    for (int c = 0; c < p->tracksCount; c++)
      printf(" %d", p->song[r][c] == EMPTY_VALUE_16 ? -1 : p->song[r][c]);
    printf("\n");
  }
  for (int ph = 0; ph < 32; ph++) {
    if (phraseIsEmpty(p.get(), ph)) continue;
    printf("phrase %d:", ph);
    for (int r = 0; r < 16; r++)
    {
      const PhraseRow& row = p->phrases[ph].rows[r];
      printf(" %s", noteName(p.get(), row.note));
      if (row.note < 254) printf("/%d", (int)row.instrument);
    }
    printf("\n");
  }
  return 0;
}
