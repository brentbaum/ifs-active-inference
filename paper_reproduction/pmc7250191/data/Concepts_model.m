%% Set up concept model
%__________________________________________________________________________
clear
close all
rng('shuffle')
%rng('default')

%% Simulation options

%set to 1 to:

%simulate multiple trials (as opposed to only 1)

trial_sequence = 1;

%remove knowledge (must enable A-matrix learning) - only choose 1 option
%-------------------------------------------------------------------------
likelihood_A_learning = 1; %enable A-matrix learning

%prevent reporting/feedback
prevent_reporting = 1;

remove_all_knowledge = 0; %all animals

%remove granularity knowledge (i.e., only know bird vs. fish) 

remove_granularity = 0;

%remove specific animal knowledge
remove_parakeet_knowledge = 1;
remove_parrot_knowledge = 1;
remove_pigeon_knowledge = 1;
remove_hawk_knowledge = 0;
remove_clownfish_knowledge = 0;
remove_whaleshark_knowledge = 0;
remove_minnow_knowledge = 0;
remove_sturgeon_knowledge = 0;



%perform bayesian model reduction (must enable D-matrix learning)
%-------------------------------------------------------------------------
prior_D_learning = 1; %enable A-matrix learning

BMR = 0;

%choose which concepts to include: 1 = include, 0 = remove
D{1} = [0 0 1 1 1 1 1 1]'; % concepts: {'Parakeet','Parrot','Pigeon', 'Hawk','Clownfish ','Manta ray','Minnow', 'Shark'}


%% generative process and prior beliefs about initial states (in terms of counts: D and d
%--------------------------------------------------------------------------
if BMR == 0
D{1} = [1 1 1 1 1 1 1 1]';           % concept:     {'Parakeet','Parrot','Pigeon', 'Hawk','Clownfish ','Manta ray','Minnow', 'Shark'}
end

D{2} = [1 0 0 0 0 0 0 0 0 0 0]'; % report:    {'start','Choose Parakeet','Choose Parrot','Choose Pigeon','Choose Hawk'
                                                            %'Choose Clownfish','Choose Manta ray','Choose Sardine','Choose  Shark','Choose Bird','Choose  Fish'}

d{1} = [1 1 1 1 1 1 1 1]';
d{2} = D{2}; 

%% mapping from hidden states to outcomes: A
%--------------------------------------------------------------------------
Nf    = numel(D);
for f = 1:Nf
    Ns(f) = numel(D{f});
end
No    = [3 3 3 4]; % outcomes
Ng    = numel(No);
for g = 1:Ng
    A{g} = zeros([No(g),Ns]);
end


%A  matrix
%--------------------------------------------------------------------------


for i = 1:Ns(2)
    A{1}(:,:,i) = [0 0 0 0 0 0 0 0;0 1 0 1 0 1 0 1;1 0 1 0 1 0 1 0]; %size
end


for i = 1:Ns(2)
    A{2}(:,:,i) = [0 0 0 0 0 0 0 0;1 1 0 0 1 1 0 0;0 0 1 1 0 0 1 1]; %color
end


for i = 1:Ns(2)
    A{3}(:,:,i) = [0 0 0 0 0 0 0 0;1 1 1 1 0 0 0 0;0 0 0 0 1 1 1 1];% wings/gills
end


A{4}(:,:,1) = [1 1 1 1 1 1 1 1; 0 0 0 0 0 0 0 0; 0 0 0 0 0 0 0 0; 0 0 0 0 0 0 0 0]; 
A{4}(:,:,2) = [0 0 0 0 0 0 0 0; 1 0 0 0 0 0 0 0; 0 1 1 1 1 1 1 1; 0 0 0 0 0 0 0 0]; 
A{4}(:,:,3) = [0 0 0 0 0 0 0 0; 0 1 0 0 0 0 0 0; 1 0 1 1 1 1 1 1; 0 0 0 0 0 0 0 0]; 
A{4}(:,:,4) = [0 0 0 0 0 0 0 0; 0 0 1 0 0 0 0 0; 1 1 0 1 1 1 1 1; 0 0 0 0 0 0 0 0]; 
A{4}(:,:,5) = [0 0 0 0 0 0 0 0; 0 0 0 1 0 0 0 0; 1 1 1 0 1 1 1 1; 0 0 0 0 0 0 0 0]; 
A{4}(:,:,6) = [0 0 0 0 0 0 0 0; 0 0 0 0 1 0 0 0; 1 1 1 1 0 1 1 1; 0 0 0 0 0 0 0 0]; 
A{4}(:,:,7) = [0 0 0 0 0 0 0 0; 0 0 0 0 0 1 0 0; 1 1 1 1 1 0 1 1; 0 0 0 0 0 0 0 0]; 
A{4}(:,:,8) = [0 0 0 0 0 0 0 0; 0 0 0 0 0 0 1 0; 1 1 1 1 1 1 0 1; 0 0 0 0 0 0 0 0]; 
A{4}(:,:,9) = [0 0 0 0 0 0 0 0; 0 0 0 0 0 0 0 1; 1 1 1 1 1 1 1 0; 0 0 0 0 0 0 0 0]; 
A{4}(:,:,10) = [0 0 0 0 0 0 0 0; 0 0 0 0 0 0 0 0; 0 0 0 0 1 1 1 1; 1 1 1 1 0 0 0 0]; 
A{4}(:,:,11) = [0 0 0 0 0 0 0 0; 0 0 0 0 0 0 0 0; 1 1 1 1 0 0 0 0; 0 0 0 0 1 1 1 1]; %feedback

for g = 1:Ng
    A{g} = double(A{g});
end
           
%% beliefs about state-outcome mappings: a

a = A;

pa = 0; % inverse temperature parameter; 0 = completely flatten state-outcome mapping distributions for concepts
           
if remove_all_knowledge == 1

%remove all concept knowledge
    a{1}(2:3,:,:)=spm_softmax(pa*log(a{1}(2:3,:,:)+exp(-4)))+ .01*randn(size(a{1}(2:3,:,:))); % only content precision
    a{2}(2:3,:,:)=spm_softmax(pa*log(a{1}(2:3,:,:)+exp(-4)))+ .01*randn(size(a{1}(2:3,:,:))); % only content precision
    a{3}(2:3,:,:)=spm_softmax(pa*log(a{1}(2:3,:,:)+exp(-4)))+ .01*randn(size(a{1}(2:3,:,:))); % Wings/gills
end

%remove granular knowledge

if remove_granularity == 1
    a{1}(2:3,:,:)=spm_softmax(pa*log(a{1}(2:3,:,:)+exp(-4)))+ .01*randn(size(a{1}(2:3,:,:))); % only content precision
    a{2}(2:3,:,:)=spm_softmax(pa*log(a{1}(2:3,:,:)+exp(-4)))+ .01*randn(size(a{1}(2:3,:,:))); % only content precision
end

if remove_parakeet_knowledge == 1
% no Parakeet
    a{1}(2:3,1,:)=spm_softmax(pa*log(a{1}(2:3,1,:)+exp(-4)))+ .01*randn(size(a{1}(2:3,1,:))); % only content precision
    a{2}(2:3,1,:)=spm_softmax(pa*log(a{1}(2:3,1,:)+exp(-4)))+ .01*randn(size(a{1}(2:3,1,:))); % only content precision
    a{3}(2:3,1,:)=spm_softmax(pa*log(a{1}(2:3,1,:)+exp(-4)))+ .01*randn(size(a{1}(2:3,1,:))); % Wings/gills
end

if remove_parrot_knowledge == 1
% no parrot
    a{1}(2:3,2,:)=spm_softmax(pa*log(a{1}(2:3,2,:)+exp(-4)))+ .01*randn(size(a{1}(2:3,2,:))); % only content precision
    a{2}(2:3,2,:)=spm_softmax(pa*log(a{1}(2:3,2,:)+exp(-4)))+ .01*randn(size(a{1}(2:3,2,:))); % only content precision
    a{3}(2:3,2,:)=spm_softmax(pa*log(a{1}(2:3,2,:)+exp(-4)))+ .01*randn(size(a{1}(2:3,2,:))); % Wings/gills
end

if remove_pigeon_knowledge == 1
 % no Pigeon
    a{1}(2:3,3,:)=spm_softmax(pa*log(a{1}(2:3,3,:)+exp(-4)))+ .01*randn(size(a{1}(2:3,3,:))); % only content precision
    a{2}(2:3,3,:)=spm_softmax(pa*log(a{1}(2:3,3,:)+exp(-4)))+ .01*randn(size(a{1}(2:3,3,:))); % only content precision
    a{3}(2:3,3,:)=spm_softmax(pa*log(a{1}(2:3,3,:)+exp(-4)))+ .01*randn(size(a{1}(2:3,3,:))); % Wings/gills
end

if remove_hawk_knowledge == 1
% no Hawk
    a{1}(2:3,4,:)=spm_softmax(pa*log(a{1}(2:3,4,:)+exp(-4)))+ .01*randn(size(a{1}(2:3,4,:))); % only content precision
    a{2}(2:3,4,:)=spm_softmax(pa*log(a{1}(2:3,4,:)+exp(-4)))+ .01*randn(size(a{1}(2:3,4,:))); % only content precision
    a{3}(2:3,4,:)=spm_softmax(pa*log(a{1}(2:3,4,:)+exp(-4)))+ .01*randn(size(a{1}(2:3,4,:))); % Wings/gills
end

if remove_clownfish_knowledge == 1
%no clown fish
    a{1}(2:3,5,:)=spm_softmax(pa*log(a{1}(2:3,5,:)+exp(-4)))+ .01*randn(size(a{1}(2:3,5,:))); % only content precision
    a{2}(2:3,5,:)=spm_softmax(pa*log(a{1}(2:3,5,:)+exp(-4)))+ .01*randn(size(a{1}(2:3,5,:))); % only content precision
    a{3}(2:3,5,:)=spm_softmax(pa*log(a{1}(2:3,5,:)+exp(-4)))+ .01*randn(size(a{1}(2:3,5,:))); % Wings/gills
end

if remove_whaleshark_knowledge == 1
%no whale shark
    a{1}(2:3,6,:)=spm_softmax(pa*log(a{1}(2:3,6,:)+exp(-4)))+ .01*randn(size(a{1}(2:3,6,:))); % only content precision
    a{2}(2:3,6,:)=spm_softmax(pa*log(a{1}(2:3,6,:)+exp(-4)))+ .01*randn(size(a{1}(2:3,6,:))); % only content precision
    a{3}(2:3,6,:)=spm_softmax(pa*log(a{1}(2:3,6,:)+exp(-4)))+ .01*randn(size(a{1}(2:3,6,:))); % Wings/gills
end

if remove_minnow_knowledge == 1

%no Minnow
    a{1}(2:3,7,:)=spm_softmax(pa*log(a{1}(2:3,7,:)+exp(-4)))+ .01*randn(size(a{1}(2:3,7,:))); % only content precision
    a{2}(2:3,7,:)=spm_softmax(pa*log(a{1}(2:3,7,:)+exp(-4)))+ .01*randn(size(a{1}(2:3,7,:))); % only content precision
    a{3}(2:3,7,:)=spm_softmax(pa*log(a{1}(2:3,7,:)+exp(-4)))+ .01*randn(size(a{1}(2:3,7,:))); % Wings/gills
end

if remove_sturgeon_knowledge == 1

%no Sturgeon
    a{1}(2:3,8,:)=spm_softmax(pa*log(a{1}(2:3,8,:)+exp(-4)))+ .01*randn(size(a{1}(2:3,8,:))); % only content precision
    a{2}(2:3,8,:)=spm_softmax(pa*log(a{1}(2:3,8,:)+exp(-4)))+ .01*randn(size(a{1}(2:3,8,:))); % only content precision
    a{3}(2:3,8,:)=spm_softmax(pa*log(a{1}(2:3,8,:)+exp(-4)))+ .01*randn(size(a{1}(2:3,8,:))); % Wings/gills

end

%% controlled transitions
%--------------------------------------------------------------------------
for f = 1:Nf
    B{f} = eye(Ns(f));
end
 
% controllable report state
%--------------------------------------------------------------------------
for k = 1:Ns(2)
    B{2}(:,:,k) = 0;
    B{2}(k,:,k) = 1;
end

B{2}(:,2:11,:) = 0;

for i = 2:11
    B{2}(i,i,:) = 1;
end


%% allowable policies (here, specified as the next action) U
%--------------------------------------------------------------------------
T = 2;
Np        = size(B{2},3);
U         = ones(1,Np-1,Nf);
U(:,:,2)  = 2:Np;


if prevent_reporting == 1

%prevent reporting
%--------------------------------------------------------------------------

U = [];
U(:,:,1)  = [1];
U(:,:,2)  = [1];

end

%% prior preferences: C
%--------------------------------------------------------------------------
C{1}      = zeros(No(1),T);
C{2}      = zeros(No(2),T);
C{3}      = zeros(No(3),T);
C{4}      = zeros(No(4),T);
C{4}(2,:) =   4;                 % Correct-Subordinate
C{4}(4,:) =   0;                 % Correct-Basic
C{4}(3,:) =  -4;                 % Incorrect




%% MDP Structure - this will be used to generate arrays for multiple trials
%==========================================================================
mdp.T = T;                      % number of moves
mdp.V = U;                     % allowable shallow policies
mdp.A = A;                      % observation model
mdp.B = B;                      % transition probabilities
mdp.C = C;                      % preferred outcomes
mdp.D = D;                      % prior over initial states

if likelihood_A_learning == 1
mdp.a = a;                      % observation beliefs
end

if prior_D_learning == 1
mdp.d = d;                     % prior beliefs over initial states
end

label.factor{1}   = 'concepts';   label.name{1}    = {'Parakeet','Parrot','Pigeon', 'Hawk','Clownfish ','Manta ray','Minnow', 'Shark'};
label.factor{2}   = 'self-reports';     label.name{2}    = {'start','Choose Parakeet','Choose Parrot','Choose Pigeon','Choose Hawk','Choose Clownfish','Choose Manta ray','Choose Sardine','Choose  Shark','Choose Bird','Choose  Fish'};
label.modality{1} = 'size';    label.outcome{1} = {'big','small'};
label.modality{2} = 'color';  label.outcome{2} = {'colorful','gray'};
label.modality{3} = 'wings/gills';    label.outcome{3} = {'wings','gills'};
label.modality{4} = 'feedback';    label.outcome{4} = {'start','correct-specific','incorrect','correct-basic'};
label.actions{1,1} = ' ';
label.actions{1,2} = ' ';
mdp.label = label;

mdp.alpha = 128;% inverse temperature for action selection
mdp.beta = 1;% prior policy precision

mdp         = spm_MDP_check(mdp);

%% illustrate a single trial
%==========================================================================
MDP   = spm_MDP_VB_X(mdp);

% show belief updates (and behaviour)
%--------------------------------------------------------------------------
spm_figure('GetWin','Figure 1'); clf
spm_MDP_VB_trial(MDP(1), 1:2,4);
subplot(3,2,3)

return
if trial_sequence == 1
%% illustrate a sequence of trials
%==========================================================================
clear MDP


N = 200;% number of learning trials
 
for i = 1:N
   MDP(i)   = mdp;      % create structure array
end

% Solve - an example sequence
%==========================================================================
MDP  = spm_MDP_VB_X(MDP);
 
% illustrate behavioural responses and neuronal correlates
%--------------------------------------------------------------------------
spm_figure('GetWin','Figure 4'); clf
spm_MDP_VB_game(MDP(1:20: N));
 
spm_figure('GetWin','Figure 6'); clf
spm_MDP_VB_LFP(MDP(1:20: N)); 

% plot A, and a (before and after learning)

if likelihood_A_learning == 1

LMA = [MDP(N).A{1}(2:3,:,1);
      MDP(N).A{2}(2:3,:,1);
      MDP(N).A{3}(2:3,:,1)];
LMa = [MDP(N).a{1}(2:3,:,1);
      MDP(N).a{2}(2:3,:,1);
      MDP(N).a{3}(2:3,:,1)];
LMa1 = [mdp.a{1}(2:3,:,1);
      mdp.a{2}(2:3,:,1);
      mdp.a{3}(2:3,:,1)]; 
  

spm_figure('GetWin','generative process'); clf
imagesc(LMA), colormap gray % generative process

spm_figure('GetWin','generative model after learning'); clf
imagesc(LMa), colormap gray % after learning

spm_figure('GetWin','generative model before learning'); clf
imagesc(LMa1), colormap gray % before learning
end


end

%% Bayesian model reduction
if BMR == 1
if prior_D_learning == 1

qA = MDP(N).d{1};
pA = d{1};
rA = [permn([1 8], 8)]';

spm_figure('GetWin','posterior distribution'); clf
imagesc(qA'), colormap gray

spm_figure('GetWin','prior distribution'); clf
imagesc(pA'), colormap gray

spm_figure('GetWin','true distribution'); clf
imagesc([MDP(N).D{1}]'), colormap gray

evidence = [];
      
for i = 1:size(rA,2)
[evidence] = [evidence spm_MDP_log_evidence(qA,pA,rA)];
end

[Min, idx] = min(evidence);
winner_evidence = Min
winner = [rA(:,idx)']

spm_figure('GetWin','winning model'); clf
imagesc(winner), colormap gray

end
end

