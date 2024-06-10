%% ジョイスティックで目標を狙う精度を図るプログラム

tic

rng('shuffle')

clear SubName;
SubName = input('Input the name of the participant:', 's');
if isempty(SubName)
    return;
end

tmpdatestr = datestr(now, 30);

% home path
home_path = pwd;

%試行数に関する設定
fontsize = 30; %フォントサイズ
intervalPractice = 1;
intervalActual = 3;
messageWaitSec = 3;
trialSum = 40; %パフォーマンスを測定する試行数
trial = struct('TargetAngle', 0, 'JoystickAngle', 0, 'Error', 0, 'SuccessFlag', false);
performanceTrialList = repmat(trial, 1, trialSum);

joycon = joystickControl();

try

    msg = 'ジョイスティックを倒して点を移動させ，バーに当ててください\n準備ができたら教えてください．';
    joycon.showMessage('Center', double(msg), true);
    joycon.waitSpace(); counter = 0; successCounter = 0; 
    for tInd = 1:trialSum
        syms f(x); 
        f = pi * rand * dirac(x); 
        [successFlag, axesArr, targetArr, originalError, joyAngleOriginal] = joycon.taskExecute(f, 'Symbolic', 0, 0, 0, true, false);
        if successFlag
            successCounter = successCounter + 1;      
        end
        performanceTrialList(tInd).TargetAngle = targetArr(1);
        performanceTrialList(tInd).JoystickAngle = joyAngleOriginal;
        performanceTrialList(tInd).Error = abs(originalError);
        performanceTrialList(tInd).SuccessFlag = successFlag;
    end

    
%     %% 保存と終了
    msg = '以上で終了です．ありがとうございました．';
    disp(strcat(int2str(successCounter), '回成功した。'));
    joycon.showMessage('Center', double(msg), true);
    joycon.waitSpace();
    trialListTable = struct2table(performanceTrialList);
    filename = sprintf('%s_%s_performance', SubName, tmpdatestr);

    save(filename, 'trialListTable');
    
    joycon.delete();
    
    toc
    
catch ME
    joycon.delete();
    trialListTable = struct2table(performanceTrialList);
    filename = sprintf('%s_%s_performance', SubName, tmpdatestr);
    save(filename, 'trialListTable');
    rethrow(ME);
end
