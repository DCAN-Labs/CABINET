import tempfile
import nibabel as nib

from img_processing.correct_chirality import correct_chirality
from util.look_up_tables import get_id_to_region_mapping


def test_correct_chirality_incorrect_left_label():
    nifti_input_file_path = '../../temp/test_subject_data/1mo/sub-00006_ses-20170806_nnUnet_aseg_pre_chircorrection.nii.gz'
    segment_lookup_table = '../../data/look_up_tables/FreeSurferColorLUT.txt'
    left_right_mask_nifti_file = '../../temp/test_subject_data/1mo/LRmask.nii.gz'
    fp = tempfile.NamedTemporaryFile(suffix='.nii.gz')
    nifti_output_file_path = fp.name
    correct_chirality(nifti_input_file_path, segment_lookup_table, left_right_mask_nifti_file,
                      nifti_output_file_path)
    incorrectly_labeled_left = (62, 91, 91)
    incorrect_right_label = 'Left-Cerebral-White-Matter'
    input_img = nib.load(nifti_input_file_path)
    input_data = input_img.get_data()
    free_surfer_label_to_region = get_id_to_region_mapping(segment_lookup_table)
    output_img = nib.load(nifti_input_file_path)
    output_data = output_img.get_data()
    assert incorrect_right_label == free_surfer_label_to_region(
            input_data[incorrectly_labeled_left[0]], [incorrectly_labeled_left[1]], [incorrectly_labeled_left[2]])
    correct_right_label = 'Right-Cerebral-White-Matter'
    assert correct_right_label == free_surfer_label_to_region(
            output_data[incorrectly_labeled_left[0]], [incorrectly_labeled_left[1]], [incorrectly_labeled_left[2]])


if __name__ == "__main__":
    test_correct_chirality_incorrect_left_label()