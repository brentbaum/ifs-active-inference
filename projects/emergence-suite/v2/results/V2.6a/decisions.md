# V2.6a decisions

1. The single latent `L_t` is a four-state HMM shared by all four relational
   channels. No channel-specific partner latent was introduced.
2. Root evidence is a separate observation whose likelihood is sharpened by
   broadcast global precision. Relational observations therefore affect
   evidence uptake but have root BF exactly one when the root channel is
   absent.
3. Stable and switching recovery histories are balanced within every family.
   A switching world's registered family is its initial and majority-occupancy
   state; its final third occupies the declared adjacent state.
4. `co_regulated` is a pure thresholded readout over posterior reliable mass
   and global precision. It is never stored as scientific state or fed back.
5. Gate 2 stopped on the frozen ECE criterion. Gate-3 seeds were not opened
   and no calibration repair or parameter tuning was attempted.
